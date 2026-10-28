from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_email_ops.app.models import Department


def suggest_department(db: Session, organization_id: int, category: str) -> Department | None:
    """The first department of the organization that handles this category, or None.

    This is plain code on purpose: the AI chooses the category, a rule chooses the department.
    """
    departments = db.scalars(
        select(Department)
        .where(Department.organization_id == organization_id)
        .order_by(Department.id)
    ).all()
    for department in departments:
        if category in department.categories:
            return department
    return None