from ai_email_ops.app.models import Department
from ai_email_ops.app.schemas import TicketDraft


def ticket_status(client, headers, ticket_id):
    tickets = client.get("/me/tickets", headers=headers).json()
    return next(t["status"] for t in tickets if t["id"] == ticket_id)


def test_reply_without_escalation_completes_the_ticket(
    client, login, make_agent, make_email, make_ticket
):
    asha = make_agent("asha")
    ticket_id = make_ticket(asha, make_email(agent=asha))
    headers = login(asha)
    assert ticket_status(client, headers, ticket_id) == "open"

    response = client.post(f"/tickets/{ticket_id}/reply", json={"body": "Hello"}, headers=headers)

    assert response.status_code == 201
    assert ticket_status(client, headers, ticket_id) == "completed"


def test_escalation_makes_ticket_pending_and_reply_keeps_it_pending(
    client, login, make_agent, make_email, make_ticket, department
):
    asha = make_agent("asha")
    ticket_id = make_ticket(asha, make_email(agent=asha))
    headers = login(asha)

    escalate = client.post(
        f"/tickets/{ticket_id}/escalate",
        json={"department_id": department.id, "body": "Please check the charge"},
        headers=headers,
    )
    assert escalate.status_code == 201
    assert ticket_status(client, headers, ticket_id) == "pending"

    reply = client.post(f"/tickets/{ticket_id}/reply", json={"body": "We are checking"}, headers=headers)
    assert reply.status_code == 201
    assert ticket_status(client, headers, ticket_id) == "pending"


def test_cannot_escalate_to_another_organizations_department(
    client, login, db, other_org, make_agent, make_email, make_ticket
):
    asha = make_agent("asha")
    ticket_id = make_ticket(asha, make_email(agent=asha))
    foreign = Department(organization_id=other_org.id, name="Accounting", email="acc@other.test")
    db.add(foreign)
    db.commit()
    db.refresh(foreign)

    response = client.post(
        f"/tickets/{ticket_id}/escalate",
        json={"department_id": foreign.id, "body": "Hello"},
        headers=login(asha),
    )

    assert response.status_code == 404


def test_start_ticket_returns_the_ai_draft(
    client, login, monkeypatch, make_agent, make_email
):
    fake_draft = TicketDraft(
        summary="Customer was charged twice.",
        category="billing",
        priority="high",
        sentiment="neutral",
        requested_action="Refund",
    )
    # Replace the real AI call (slow, unpredictable) with a fake that returns our draft
    monkeypatch.setattr(
        "ai_email_ops.app.routes_emails.extract_ticket_draft", lambda email: fake_draft
    )
    asha = make_agent("asha")
    email = make_email(agent=asha)

    response = client.post(f"/emails/{email.id}/start-ticket", headers=login(asha))

    assert response.status_code == 200
    assert response.json()["category"] == "billing"

def make_fake_extract(calls):
    def fake_extract(email):
        calls.append(email.id)
        return TicketDraft(
            summary="Customer was charged twice.",
            category="billing",
            priority="high",
            sentiment="neutral",
            requested_action="Refund",
        )

    return fake_extract


def test_second_start_ticket_uses_the_cache(
    client, login, monkeypatch, make_agent, make_email
):
    calls = []
    monkeypatch.setattr(
        "ai_email_ops.app.routes_emails.extract_ticket_draft", make_fake_extract(calls)
    )
    asha = make_agent("asha")
    email = make_email(agent=asha)
    headers = login(asha)

    client.post(f"/emails/{email.id}/start-ticket", headers=headers)
    client.post(f"/emails/{email.id}/start-ticket", headers=headers)
    assert len(calls) == 1  # the AI ran only once

    client.post(f"/emails/{email.id}/start-ticket?refresh=true", headers=headers)
    assert len(calls) == 2  # refresh forces a new AI call


def test_cached_draft_is_not_visible_to_another_agent(
    client, login, monkeypatch, make_agent, make_email
):
    monkeypatch.setattr(
        "ai_email_ops.app.routes_emails.extract_ticket_draft", make_fake_extract([])
    )
    asha = make_agent("asha")
    ben = make_agent("ben")
    email = make_email(agent=asha)

    client.post(f"/emails/{email.id}/start-ticket", headers=login(asha))  # fills the cache
    response = client.post(f"/emails/{email.id}/start-ticket", headers=login(ben))

    assert response.status_code == 403