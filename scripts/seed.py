from passlib.context import CryptContext

from ai_email_ops.app.db import SessionLocal
from ai_email_ops.app.models import Organization, SupportAgent

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main() -> None:
    with SessionLocal() as db:
        org = Organization(name="Acme Corp")
        db.add(org)
        db.flush()  # sends the INSERT now so org.id gets filled in
        for name in ["Asha", "Ben", "Chen"]:
            db.add(
                SupportAgent(
                    organization_id=org.id,
                    name=name,
                    email=f"{name.lower()}@acme.test",
                    hashed_password=pwd_context.hash("password123"),
                )
            )
        db.commit()
        print(f"Created organization id={org.id}")


main()