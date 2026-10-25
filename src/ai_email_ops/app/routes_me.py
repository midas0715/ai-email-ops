from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ai_email_ops.app.db import get_db
from ai_email_ops.app.deps import get_current_agent
from ai_email_ops.app.models import Department, Email, SupportAgent, Ticket, TicketStatus
from ai_email_ops.app.schemas import TicketDraft

router = APIRouter(prefix="/me", tags=["me"])


class AgentProfile(BaseModel):
    id: int
    name: str
    email: str
    organization_id: int
    organization_name: str


class EmailItem(BaseModel):
    id: int
    sender_email: str
    subject: str
    received_at: datetime
    has_ticket: bool


class EmailDetail(BaseModel):
    id: int
    sender_email: str
    subject: str
    body: str
    received_at: datetime
    ticket_id: int | None


class TicketItem(BaseModel):
    id: int
    email_id: int
    subject: str
    status: TicketStatus
    data: TicketDraft
    created_at: datetime


class ReplyInfo(BaseModel):
    to_email: str
    subject: str
    body: str
    sent_at: datetime

    model_config = {"from_attributes": True}


class EscalationInfo(BaseModel):
    department_id: int
    department: str
    to_email: str
    subject: str
    body: str
    sent_at: datetime


class TicketDetail(BaseModel):
    id: int
    status: TicketStatus
    data: TicketDraft
    created_at: datetime
    updated_at: datetime
    email: EmailDetail
    reply: ReplyInfo | None
    escalation: EscalationInfo | None


class DepartmentItem(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


def email_detail(email: Email) -> EmailDetail:
    return EmailDetail(
        id=email.id,
        sender_email=email.sender_email,
        subject=email.subject,
        body=email.body,
        received_at=email.received_at,
        ticket_id=email.ticket.id if email.ticket else None,
    )


@router.get("", response_model=AgentProfile)
def my_profile(agent: SupportAgent = Depends(get_current_agent)):
    return AgentProfile(
        id=agent.id,
        name=agent.name,
        email=agent.email,
        organization_id=agent.organization_id,
        organization_name=agent.organization.name,
    )


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


@router.get("/emails/{email_id}", response_model=EmailDetail)
def my_email(
    email_id: int,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    email = db.get(Email, email_id)
    # someone else's email looks exactly like a missing one
    if email is None or email.assigned_agent_id != agent.id:
        raise HTTPException(status_code=404, detail="Email not found")
    return email_detail(email)


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
        .options(selectinload(Ticket.email))  # the subject lives on the email
        .order_by(Ticket.created_at.desc(), Ticket.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if status is not None:
        stmt = stmt.where(Ticket.status == status)

    tickets = db.scalars(stmt).all()
    return [
        TicketItem(
            id=t.id,
            email_id=t.email_id,
            subject=t.email.subject,
            status=t.status,
            data=t.data,
            created_at=t.created_at,
        )
        for t in tickets
    ]


@router.get("/tickets/{ticket_id}", response_model=TicketDetail)
def my_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or ticket.agent_id != agent.id:
        raise HTTPException(status_code=404, detail="Ticket not found")

    escalation = None
    if ticket.escalation is not None:
        e = ticket.escalation
        escalation = EscalationInfo(
            department_id=e.department_id,
            department=e.department.name,
            to_email=e.to_email,
            subject=e.subject,
            body=e.body,
            sent_at=e.sent_at,
        )

    return TicketDetail(
        id=ticket.id,
        status=ticket.status,
        data=ticket.data,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        email=email_detail(ticket.email),
        reply=ReplyInfo.model_validate(ticket.reply) if ticket.reply else None,
        escalation=escalation,
    )


@router.get("/departments", response_model=list[DepartmentItem])
def my_departments(
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    """The departments an agent can escalate to: those of their own organization."""
    stmt = (
        select(Department)
        .where(Department.organization_id == agent.organization_id)
        .order_by(Department.name)
    )
    return db.scalars(stmt).all()