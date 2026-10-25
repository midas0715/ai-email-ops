from ai_email_ops.app.models import Department

ORIGIN = "http://localhost:5173"


def test_profile_shows_name_and_organization(client, login, make_agent):
    asha = make_agent("asha")

    response = client.get("/me", headers=login(asha))

    assert response.status_code == 200
    assert response.json()["name"] == "asha"
    assert response.json()["organization_name"] == "Test Org"


def test_profile_needs_a_token(client):
    assert client.get("/me").status_code == 401


def test_agent_reads_own_email_with_body(client, login, make_agent, make_email):
    asha = make_agent("asha")
    email = make_email(agent=asha)

    response = client.get(f"/me/emails/{email.id}", headers=login(asha))

    assert response.status_code == 200
    assert response.json()["body"] == "I was charged twice for my order."
    assert response.json()["ticket_id"] is None


def test_agent_cannot_read_another_agents_email(client, login, make_agent, make_email):
    asha = make_agent("asha")
    ben = make_agent("ben")
    email = make_email(agent=asha)

    assert client.get(f"/me/emails/{email.id}", headers=login(ben)).status_code == 404


def test_agent_sees_only_departments_of_own_organization(
    client, login, db, other_org, make_agent, department
):
    db.add(Department(organization_id=other_org.id, name="Legal", email="legal@other.test"))
    db.commit()
    asha = make_agent("asha")

    response = client.get("/me/departments", headers=login(asha))

    assert response.status_code == 200
    assert [d["name"] for d in response.json()] == ["Accounting"]


def test_ticket_list_includes_the_email_subject(
    client, login, make_agent, make_email, make_ticket
):
    asha = make_agent("asha")
    make_ticket(asha, make_email(agent=asha))

    response = client.get("/me/tickets", headers=login(asha))

    assert response.json()[0]["subject"] == "Refund request"


def test_ticket_detail_shows_email_reply_and_escalation(
    client, login, make_agent, make_email, make_ticket, department
):
    asha = make_agent("asha")
    ticket_id = make_ticket(asha, make_email(agent=asha))
    headers = login(asha)

    fresh = client.get(f"/me/tickets/{ticket_id}", headers=headers).json()
    assert fresh["reply"] is None and fresh["escalation"] is None

    client.post(
        f"/tickets/{ticket_id}/escalate",
        json={"department_id": department.id, "body": "Please check"},
        headers=headers,
    )
    client.post(f"/tickets/{ticket_id}/reply", json={"body": "We are checking"}, headers=headers)

    detail = client.get(f"/me/tickets/{ticket_id}", headers=headers).json()
    assert detail["status"] == "pending"
    assert detail["email"]["body"] == "I was charged twice for my order."
    assert detail["reply"]["body"] == "We are checking"
    assert detail["escalation"]["department"] == "Accounting"


def test_ticket_detail_of_another_agent_is_404(
    client, login, make_agent, make_email, make_ticket
):
    asha = make_agent("asha")
    ben = make_agent("ben")
    ticket_id = make_ticket(asha, make_email(agent=asha))

    assert client.get(f"/me/tickets/{ticket_id}", headers=login(ben)).status_code == 404


def test_cors_allows_the_frontend_and_nobody_else(client):
    asked = {
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization",
    }

    allowed = client.options("/me/emails", headers={"Origin": ORIGIN, **asked})
    stranger = client.options("/me/emails", headers={"Origin": "http://evil.example", **asked})

    assert allowed.headers["access-control-allow-origin"] == ORIGIN
    assert "access-control-allow-origin" not in stranger.headers