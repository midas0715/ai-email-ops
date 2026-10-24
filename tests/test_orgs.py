from ai_email_ops.app.security import ROLE_AGENT, ROLE_ORG, create_access_token

ORG = {"name": "Globex", "email": "ceo@globex-corp.com", "password": "supersecret1"}


def register(client, **override):
    return client.post("/orgs/register", json={**ORG, **override})


def org_headers(client):
    response = client.post(
        "/auth/org-login", data={"username": ORG["email"], "password": ORG["password"]}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_register_returns_org_without_any_password(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ceo@globex-corp.com"
    assert "password" not in body and "hashed_password" not in body


def test_duplicate_name_or_email_is_409(client):
    assert register(client).status_code == 201
    assert register(client).status_code == 409  # same name and email
    assert register(client, name="Another Name").status_code == 409  # same email


def test_short_password_is_422(client):
    assert register(client, password="short").status_code == 422


def test_org_can_log_in_and_read_its_profile(client):
    register(client)

    response = client.get("/orgs/me", headers=org_headers(client))

    assert response.status_code == 200
    assert response.json()["name"] == "Globex"


def test_org_login_with_wrong_password_is_401(client):
    register(client)

    response = client.post(
        "/auth/org-login", data={"username": ORG["email"], "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_token_role_is_checked(client, org, make_agent, make_email):
    asha = make_agent("asha")
    email = make_email(agent=asha)

    # A token with the right id (asha's) but the WRONG role must not work on an agent route
    org_style = {"Authorization": f"Bearer {create_access_token(asha.id, ROLE_ORG)}"}
    response = client.post(f"/emails/{email.id}/start-ticket", headers=org_style)
    assert response.status_code == 401

    # A token with an existing organization id but the WRONG role must not work on an org route
    agent_style = {"Authorization": f"Bearer {create_access_token(org.id, ROLE_AGENT)}"}
    assert client.get("/orgs/me", headers=agent_style).status_code == 401