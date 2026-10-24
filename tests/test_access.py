def test_no_token_is_rejected(client, make_agent, make_email):
    asha = make_agent("asha")
    email = make_email(agent=asha)

    response = client.post(f"/emails/{email.id}/start-ticket")

    assert response.status_code == 401


def test_wrong_password_is_rejected(client, make_agent):
    asha = make_agent("asha")

    response = client.post("/auth/login", data={"username": asha.email, "password": "wrong"})

    assert response.status_code == 401


def test_agent_cannot_start_ticket_on_another_agents_email(
    client, login, make_agent, make_email
):
    asha = make_agent("asha")
    ben = make_agent("ben")
    email = make_email(agent=asha)

    response = client.post(f"/emails/{email.id}/start-ticket", headers=login(ben))

    assert response.status_code == 403


def test_second_ticket_for_same_email_is_409(client, login, draft, make_agent, make_email):
    asha = make_agent("asha")
    email = make_email(agent=asha)
    headers = login(asha)

    first = client.post(f"/emails/{email.id}/ticket", json=draft, headers=headers)
    second = client.post(f"/emails/{email.id}/ticket", json=draft, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 409


def test_my_tickets_only_shows_own_tickets(
    client, login, make_agent, make_email, make_ticket
):
    asha = make_agent("asha")
    ben = make_agent("ben")
    make_ticket(asha, make_email(agent=asha))

    response = client.get("/me/tickets", headers=login(ben))

    assert response.status_code == 200
    assert response.json() == []