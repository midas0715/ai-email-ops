from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ai_email_ops.app.models import Email, SupportAgent


def pick_random_agent(db: Session, organization_id: int) -> SupportAgent | None:
    """Return one random active agent of the organization, or None if there is none."""
    stmt = (
        select(SupportAgent)
        .where(
            SupportAgent.organization_id == organization_id,
            SupportAgent.is_active.is_(True),
        )
        .order_by(func.random())
        .limit(1)
    )
    return db.scalars(stmt).first()


def assign_email(db: Session, email: Email) -> Email:
    """Assign the email to a random agent. Safe to call twice."""
    if email.assigned_agent_id is not None:
        return email  # already assigned, do nothing

    agent = pick_random_agent(db, email.organization_id)
    if agent is None:
        return email  # no active agents: stays unassigned for now

    email.assigned_agent_id = agent.id
    db.commit()
    db.refresh(email)
    return email