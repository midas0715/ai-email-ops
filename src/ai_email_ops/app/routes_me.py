from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ai_email_ops.app.db import get_db
from ai_email_ops.app.deps import get_current_agent
from ai_email_ops.app.models import Email, SupportAgent, Ticket, TicketStatus
from ai_email_ops.app.schemas import TicketDraft

router = APIRouter(prefix="/me", tags=["me"])


class EmailItem(BaseModel):
    id: int
    sender_email: str
    subject: str
    received_at: datetime
    has_ticket: bool


class TicketItem(BaseModel):
    id: int
    email_id: int
    status: TicketStatus
    data: TicketDraft
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/emails", response_model=list[EmailItem])
def my_emails(
    only_new: bool = False,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    stmt = (
        select(Email)
        .where(Email.assigned_agent_id == agent.id)
        .options(selectinload(Email.ticket))  # load all tickets in one extra query
        .order_by(Email.received_at.desc(), Email.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if only_new:
        stmt = stmt.where(~Email.ticket.has())  # emails with no ticket yet

    emails = db.scalars(stmt).all()
    return [
        EmailItem(
            id=e.id,
            sender_email=e.sender_email,
            subject=e.subject,
            received_at=e.received_at,
            has_ticket=e.ticket is not None,
        )
        for e in emails
    ]


@router.get("/tickets", response_model=list[TicketItem])
def my_tickets(
    status: TicketStatus | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    stmt = (
        select(Ticket)
        .where(Ticket.agent_id == agent.id)
        .order_by(Ticket.created_at.desc(), Ticket.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if status is not None:
        stmt = stmt.where(Ticket.status == status)
    return db.scalars(stmt).all()