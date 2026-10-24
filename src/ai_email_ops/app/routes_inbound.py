from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai_email_ops.app.assignment import assign_email
from ai_email_ops.app.db import get_db
from ai_email_ops.app.deps import get_org_from_api_key
from ai_email_ops.app.models import Email, Organization

router = APIRouter(prefix="/inbound", tags=["inbound"])


class InboundEmailIn(BaseModel):
    # Real senders can look odd, so we only check size here, not the email format
    sender_email: str = Field(min_length=3, max_length=320)
    subject: str = Field(default="(no subject)", max_length=500)  # the database column holds 500
    body: str = Field(min_length=1, max_length=20000)  # protects the database and the LLM


class InboundEmailOut(BaseModel):
    id: int
    status: str = "received"


@router.post("/emails", response_model=InboundEmailOut, status_code=201)
def receive_email(
    payload: InboundEmailIn,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_org_from_api_key),
):
    email = Email(
        organization_id=org.id,  # comes from the KEY, never from the request body
        sender_email=payload.sender_email.strip(),
        subject=payload.subject.strip() or "(no subject)",
        body=payload.body,
    )
    db.add(email)
    db.commit()
    db.refresh(email)
    assign_email(db, email)
    return InboundEmailOut(id=email.id)