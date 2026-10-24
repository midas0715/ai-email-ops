from ai_email_ops.app.assignment import assign_email


def test_assigns_only_an_active_agent_of_the_same_organization(
    db, make_agent, make_email, other_org
):
    active = make_agent("asha")
    make_agent("ben", is_active=False)  # inactive: must be skipped
    make_agent("chen", organization=other_org)  # other company: must be skipped
    email = make_email()

    assign_email(db, email)

    # Only one agent is eligible, so the result is certain even though the pick is random
    assert email.assigned_agent_id == active.id


def test_no_active_agents_leaves_email_unassigned(db, make_agent, make_email):
    make_agent("ben", is_active=False)
    email = make_email()

    assign_email(db, email)

    assert email.assigned_agent_id is None


def test_already_assigned_email_is_not_reassigned(db, make_agent, make_email):
    asha = make_agent("asha")
    make_agent("ben")
    email = make_email(agent=asha)

    for _ in range(10):
        assign_email(db, email)

    assert email.assigned_agent_id == asha.id