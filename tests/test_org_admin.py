from ai_email_ops.app.security import ROLE_ORG, create_access_token

NEW_AGENT = {"name": "Dana", "email": "dana@globex-corp.com", "password": "supersecret1"}


def org_auth(org):
    return {"Authorization": f"Bearer {create_access_token(org.id, ROLE_ORG)}"}


def test_ceo_creates_agent_who_can_log_in(client, org):
    created = client.post("/orgs/me/agents", json=NEW_AGENT, headers=org_auth(org))

    assert created.status_code == 201
    assert "password" not in created.json() and "hashed_password" not in created.json()
    login = client.post(
        "/auth/login", data={"username": NEW_AGENT["email"], "password": NEW_AGENT["password"]}
    )
    assert login.status_code == 200
    listed = client.get("/orgs/me/agents", headers=org_auth(org)).json()
    assert [a["email"] for a in listed] == ["dana@globex-corp.com"]


def test_duplicate_agent_email_is_409(client, org):
    assert client.post("/orgs/me/agents", json=NEW_AGENT, headers=org_auth(org)).status_code == 201
    assert client.post("/orgs/me/agents", json=NEW_AGENT, headers=org_auth(org)).status_code == 409


def test_agent_token_cannot_manage_agents(client, login, make_agent):
    asha = make_agent("asha")

    response = client.post("/orgs/me/agents", json=NEW_AGENT, headers=login(asha))

    assert response.status_code == 401


def test_cannot_remove_agent_of_another_organization(client, org, other_org, make_agent):
    foreign = make_agent("zed", organization=other_org)

    response = client.delete(f"/orgs/me/agents/{foreign.id}", headers=org_auth(org))

    assert response.status_code == 404


def test_cannot_remove_agent_with_unfinished_ticket(
    client, org, make_agent, make_email, make_ticket
):
    asha = make_agent("asha")
    make_ticket(asha, make_email(agent=asha))

    response = client.delete(f"/orgs/me/agents/{asha.id}", headers=org_auth(org))

    assert response.status_code == 409


def test_removing_agent_moves_untouched_emails_to_others(
    client, db, org, make_agent, make_email
):
    asha = make_agent("asha")
    ben = make_agent("ben")
    first = make_email(agent=asha)
    second = make_email(agent=asha)

    response = client.delete(f"/orgs/me/agents/{asha.id}", headers=org_auth(org))

    assert response.status_code == 200
    assert response.json()["reassigned_emails"] == 2
    db.refresh(first)
    db.refresh(second)
    db.refresh(asha)
    assert first.assigned_agent_id == ben.id
    assert second.assigned_agent_id == ben.id
    assert asha.is_active is False


def test_removed_agent_is_locked_out_immediately(client, login, org, make_agent):
    asha = make_agent("asha")
    old_headers = login(asha)

    assert client.delete(f"/orgs/me/agents/{asha.id}", headers=org_auth(org)).status_code == 200

    again = client.post("/auth/login", data={"username": asha.email, "password": "password123"})
    assert again.status_code == 401
    assert client.get("/me/emails", headers=old_headers).status_code == 401  # old token is dead too


def test_cannot_remove_last_agent_who_has_waiting_emails(client, org, make_agent, make_email):
    asha = make_agent("asha")
    make_email(agent=asha)

    response = client.delete(f"/orgs/me/agents/{asha.id}", headers=org_auth(org))

    assert response.status_code == 409


def test_department_create_list_delete(client, org):
    body = {"name": "HR", "email": "hr@globex-corp.com"}
    created = client.post("/orgs/me/departments", json=body, headers=org_auth(org))
    assert created.status_code == 201
    assert client.post("/orgs/me/departments", json=body, headers=org_auth(org)).status_code == 409

    department_id = created.json()["id"]
    assert client.delete(f"/orgs/me/departments/{department_id}", headers=org_auth(org)).status_code == 204
    assert client.get("/orgs/me/departments", headers=org_auth(org)).json() == []


def test_cannot_delete_department_used_by_an_escalation(
    client, login, org, make_agent, make_email, make_ticket, department
):
    asha = make_agent("asha")
    ticket_id = make_ticket(asha, make_email(agent=asha))
    client.post(
        f"/tickets/{ticket_id}/escalate",
        json={"department_id": department.id, "body": "Please check"},
        headers=login(asha),
    )

    response = client.delete(f"/orgs/me/departments/{department.id}", headers=org_auth(org))

    assert response.status_code == 409