from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_email_ops.app.ai_extraction import extract_ticket_draft
from ai_email_ops.app.assignment import assign_email
from ai_email_ops.app.db import get_db
from ai_email_ops.app.deps import get_current_agent
from ai_email_ops.app.models import Email, Organization, SupportAgent, Ticket, TicketStatus
from ai_email_ops.app.reply_draft import draft_reply
from ai_email_ops.app.schemas import ReplyDraft, TicketDraft

from ai_email_ops.app.cache import (
    TICKET_DRAFT_TTL_SECONDS,
    cache_delete,
    cache_get,
    cache_set,
    ticket_draft_key,
)

router = APIRouter(prefix="/emails", tags=["emails"])


class EmailIn(BaseModel):
    organization_id: int
    sender_email: str
    subject: str
    body: str


class EmailOut(BaseModel):
    id: int
    organization_id: int
    assigned_agent_id: int | None
    subject: str

    model_config = {"from_attributes": True}


class TicketOut(BaseModel):
    id: int
    email_id: int
    agent_id: int
    status: TicketStatus
    data: TicketDraft

    model_config = {"from_attributes": True}


def get_own_email_or_error(db: Session, email_id: int, agent: SupportAgent) -> Email:
    """Load the email, or raise 404 (missing) / 403 (assigned to another agent)."""
    email = db.get(Email, email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    if email.assigned_agent_id != agent.id:
        raise HTTPException(status_code=403, detail="This email is assigned to another agent")
    return email


@router.post("", response_model=EmailOut)
def receive_email(payload: EmailIn, db: Session = Depends(get_db)):
    if db.get(Organization, payload.organization_id) is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    email = Email(**payload.model_dump())
    db.add(email)
    db.commit()
    db.refresh(email)
    return assign_email(db, email)


@router.post("/{email_id}/start-ticket", response_model=TicketDraft)
def start_ticket(
    email_id: int,
    refresh: bool = False,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    email = get_own_email_or_error(db, email_id, agent)  # access check FIRST, before the cache
    if email.ticket is not None:
        raise HTTPException(status_code=409, detail="This email already has a ticket")

    key = ticket_draft_key(email.id)
    if not refresh:
        cached = cache_get(key)
        if cached is not None:
            return TicketDraft.model_validate(cached)

    try:
        draft = extract_ticket_draft(email)
    except ValidationError:
        raise HTTPException(status_code=502, detail="AI returned invalid data, try again")
    except ConnectionError:
        raise HTTPException(status_code=503, detail="AI service (Ollama) is not reachable")

    cache_set(key, draft.model_dump(mode="json"), TICKET_DRAFT_TTL_SECONDS)
    return draft

@router.post("/{email_id}/ticket", response_model=TicketOut, status_code=201)
def save_ticket(
    email_id: int,
    draft: TicketDraft,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    email = get_own_email_or_error(db, email_id, agent)

    ticket = Ticket(
        email_id=email.id,
        agent_id=agent.id,
        data=draft.model_dump(mode="json"),
    )
    db.add(ticket)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This email already has a ticket")
    db.refresh(ticket)
    db.refresh(ticket)
    cache_delete(ticket_draft_key(email.id))
    return ticket


@router.post("/{email_id}/draft-reply", response_model=ReplyDraft)
def create_reply_draft(
    email_id: int,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    email = get_own_email_or_error(db, email_id, agent)

    try:
        reply, sources = draft_reply(email)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="AI service (Ollama) is not reachable")
    return ReplyDraft(reply=reply, sources=sources)