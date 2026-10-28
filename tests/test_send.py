import pytest

from ai_email_ops.app.models import Department
from ai_email_ops.app.security import ROLE_ORG, create_access_token


def org_auth(org):
    return {"Authorization": f"Bearer {create_access_token(org.id, ROLE_ORG)}"}


def add_department(db, org, name, email, categories):
    department = Department(
        organization_id=org.id, name=name, email=email, categories=categories
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@pytest.fixture
def sent(monkeypatch):
    """Replace the fake sender with a list, so tests can see which emails went out."""
    emails = []
    monkeypatch.setattr(
        "ai_email_ops.app.routes_tickets.send_email",
        lambda to, subject, body: emails.append((to, subject, body)),
    )
    return emails


def test_send_reply_and_department_notice_completes_the_ticket(
    client, login, sent, make_agent, make_email, make_ticket, department
):
    asha = make_agent("asha")
    ticket_id = make_ticket(asha, make_email(agent=asha))
    headers = login(asha)

    response = client.post(
        f"/tickets/{ticket_id}/send",
        json={
            "reply_body": "We are looking into it.",
            "department_id": department.id,
            "department_body": "Please check this charge.",
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "completed"
    assert response.json()["department_notified"] == "Accounting"
    assert [to for to, _, _ in sent] == ["customer@example.com", "accounting@test.test"]
    detail = client.get(f"/me/tickets/{ticket_id}", headers=headers).json()
    assert detail["status"] == "completed"
    assert detail["reply"]["body"] == "We are looking into it."
    assert detail["escalation"]["department"] == "Accounting"


def test_reply_only_when_no_department_is_needed(
    client, login, sent, make_agent, make_email, make_ticket
):
    asha = make_agent("asha")
    ticket_id = make_ticket(asha, make_email(agent=asha))

    response = client.post(
        f"/tickets/{ticket_id}/send", json={"reply_body": "Hello!"}, headers=login(asha)
    )

    assert response.status_code == 201
    assert response.json()["department_notified"] is None
    assert len(sent) == 1


def test_department_fields_must_come_together(
    client, login, sent, make_agent, make_email, make_ticket, department
):
    asha = make_agent("asha")
    ticket_id = make_ticket(asha, make_email(agent=asha))
    headers = login(asha)
    url = f"/tickets/{ticket_id}/send"

    only_id = client.post(
        url, json={"reply_body": "Hi", "department_id": department.id}, headers=headers
    )
    only_text = client.post(
        url, json={"reply_body": "Hi", "department_body": "Please check"}, headers=headers
    )

    assert only_id.status_code == 422
    assert only_text.status_code == 422
    assert sent == []


def test_sending_twice_is_409(client, login, sent, make_agent, make_email, make_ticket):
    asha = make_agent("asha")
    ticket_id = make_ticket(asha, make_email(agent=asha))
    headers = login(asha)

    first = client.post(f"/tickets/{ticket_id}/send", json={"reply_body": "Hi"}, headers=headers)
    second = client.post(f"/tickets/{ticket_id}/send", json={"reply_body": "Hi"}, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 409
    assert len(sent) == 1


def test_cannot_notify_another_organizations_department(
    client, login, db, sent, other_org, make_agent, make_email, make_ticket
):
    asha = make_agent("asha")
    ticket_id = make_ticket(asha, make_email(agent=asha))
    foreign = add_department(db, other_org, "Accounting", "acc@other.test", ["billing"])
    headers = login(asha)

    response = client.post(
        f"/tickets/{ticket_id}/send",
        json={"reply_body": "Hi", "department_id": foreign.id, "department_body": "Check"},
        headers=headers,
    )

    assert response.status_code == 404
    assert sent == []  # nothing was sent
    detail = client.get(f"/me/tickets/{ticket_id}", headers=headers).json()
    assert detail["status"] == "open" and detail["reply"] is None  # and nothing was saved


def test_another_agent_cannot_send_for_the_ticket(
    client, login, sent, make_agent, make_email, make_ticket
):
    asha = make_agent("asha")
    ben = make_agent("ben")
    ticket_id = make_ticket(asha, make_email(agent=asha))

    response = client.post(
        f"/tickets/{ticket_id}/send", json={"reply_body": "Hi"}, headers=login(ben)
    )

    assert response.status_code == 403
    assert sent == []


def test_ceo_sets_which_categories_a_department_handles(client, org):
    created = client.post(
        "/orgs/me/departments",
        json={
            "name": "Tech",
            "email": "tech@globex-corp.com",
            "categories": ["technical", "technical"],
        },
        headers=org_auth(org),
    )
    assert created.status_code == 201
    assert created.json()["categories"] == ["technical"]  # duplicates removed

    changed = client.put(
        f"/orgs/me/departments/{created.json()['id']}/categories",
        json={"categories": ["technical", "account"]},
        headers=org_auth(org),
    )
    assert changed.json()["categories"] == ["account", "technical"]

    bad = client.put(
        f"/orgs/me/departments/{created.json()['id']}/categories",
        json={"categories": ["banana"]},
        headers=org_auth(org),
    )
    assert bad.status_code == 422


def test_ticket_detail_suggests_the_department_for_its_category(
    client, login, db, org, make_agent, make_email, draft
):
    accounting = add_department(db, org, "Accounting", "acc@test.test", ["billing"])
    tech = add_department(db, org, "Tech", "tech@test.test", ["technical"])
    asha = make_agent("asha")
    headers = login(asha)

    def suggestion_for(category):
        email = make_email(agent=asha)
        saved = client.post(
            f"/emails/{email.id}/ticket", json={**draft, "category": category}, headers=headers
        )
        detail = client.get(f"/me/tickets/{saved.json()['id']}", headers=headers)
        return detail.json()["suggested_department_id"]

    assert suggestion_for("billing") == accounting.id
    assert suggestion_for("technical") == tech.id
    assert suggestion_for("general") is None