from ai_email_ops.app.db import SessionLocal
from ai_email_ops.app.models import Department

DEPARTMENTS = [
    ("Accounting", "accounting@acme.test"),
    ("Logistics", "logistics@acme.test"),
    ("HR", "hr@acme.test"),
    ("Engineering", "engineering@acme.test"),
]


def main() -> None:
    with SessionLocal() as db:
        for name, email in DEPARTMENTS:
            db.add(Department(organization_id=1, name=name, email=email))
        db.commit()
        print(f"Created {len(DEPARTMENTS)} departments")


main()