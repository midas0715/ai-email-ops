from ai_email_ops.app.models import Email
from ai_email_ops.app.security import ROLE_ORG, create_access_token

PAYLOAD = {"sender_email": "customer@example.com", "subject": "Refund", "body": "Charged twice"}


def org_auth(org):
    return {"Authorization": f"Bearer {create_access_token(org.id, ROLE_ORG)}"}


def make_key(client, org):
    response = client.post("/orgs/me/api-key", headers=org_auth(org))
    assert response.status_code == 201
    return response.json()["api_key"]


def send(client, key, payload=PAYLOAD):
    return client.post("/inbound/emails", json=payload, headers={"X-API-Key": key})


def test_key_is_shown_once_and_only_its_hash_is_stored(client, db, org):
    key = make_key(client, org)

    db.refresh(org)
    assert org.api_key_hash is not None and org.api_key_hash != key
    profile = client.get("/orgs/me", headers=org_auth(org))
    assert profile.json()["api_key_hint"] == key[-4:]
    assert key not in profile.text


def test_email_is_stored_for_the_key_owner_and_assigned(client, db, org, make_agent):
    asha = make_agent("asha")
    key = make_key(client, org)

    response = send(client, key)

    assert response.status_code == 201
    email = db.get(Email, response.json()["id"])
    assert email.organization_id == org.id
    assert email.assigned_agent_id == asha.id


def test_missing_or_wrong_key_is_401(client, org):
    make_key(client, org)

    assert client.post("/inbound/emails", json=PAYLOAD).status_code == 401
    assert send(client, "eok_not-a-real-key").status_code == 401


def test_new_key_replaces_old_one_and_revoke_works(client, org):
    old = make_key(client, org)
    new = make_key(client, org)

    assert send(client, old).status_code == 401
    assert send(client, new).status_code == 201

    assert client.delete("/orgs/me/api-key", headers=org_auth(org)).status_code == 204
    assert send(client, new).status_code == 401


def test_organization_id_in_the_body_is_ignored(client, db, org, other_org):
    key = make_key(client, org)

    response = send(client, key, {**PAYLOAD, "organization_id": other_org.id})

    assert response.status_code == 201
    assert db.get(Email, response.json()["id"]).organization_id == org.id


def test_oversized_input_is_rejected(client, org):
    key = make_key(client, org)

    assert send(client, key, {**PAYLOAD, "subject": "s" * 501}).status_code == 422
    assert send(client, key, {**PAYLOAD, "body": "b" * 20001}).status_code == 422


def test_agent_token_cannot_create_an_api_key(client, login, make_agent):
    asha = make_agent("asha")

    assert client.post("/orgs/me/api-key", headers=login(asha)).status_code == 401