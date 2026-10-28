from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_email_ops.app.db import get_db
from ai_email_ops.app.deps import get_current_agent
from ai_email_ops.app.escalation_draft import draft_escalation
from ai_email_ops.app.models import (
    Department,
    Escalation,
    Reply,
    SupportAgent,
    Ticket,
    TicketStatus,
)
from ai_email_ops.app.sender import send_email

router = APIRouter(prefix="/tickets", tags=["tickets"])


class ReplyIn(BaseModel):
    body: str = Field(min_length=1)


class ReplyOut(BaseModel):
    id: int
    ticket_id: int
    to_email: str
    subject: str
    body: str
    sent_at: datetime

    model_config = {"from_attributes": True}


class DepartmentChoice(BaseModel):
    department_id: int


class EscalationDraft(BaseModel):
    department: str
    to_email: str
    subject: str
    body: str


class EscalationIn(BaseModel):
    department_id: int
    body: str = Field(min_length=1)


class EscalationOut(BaseModel):
    id: int
    ticket_id: int
    department_id: int
    to_email: str
    subject: str
    body: str
    sent_at: datetime

    model_config = {"from_attributes": True}


class TicketStatusOut(BaseModel):
    id: int
    status: TicketStatus

    model_config = {"from_attributes": True}


class SendIn(BaseModel):
    reply_body: str = Field(min_length=1, max_length=20000)
    department_id: int | None = None
    department_body: str | None = Field(default=None, min_length=1, max_length=20000)

    @model_validator(mode="after")
    def department_fields_go_together(self):
        if (self.department_id is None) != (self.department_body is None):
            raise ValueError("department_id and department_body must be given together")
        return self


class SendOut(BaseModel):
    ticket_id: int
    status: TicketStatus
    reply_sent_to: str
    department_notified: str | None


def get_ticket_or_404(db: Session, ticket_id: int, agent: SupportAgent) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.agent_id != agent.id:
        raise HTTPException(status_code=403, detail="This ticket belongs to another agent")
    return ticket


def get_department_or_404(db: Session, ticket: Ticket, department_id: int) -> Department:
    department = db.get(Department, department_id)
    # the department must belong to the SAME organization as the ticket
    if department is None or department.organization_id != ticket.email.organization_id:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


def escalation_subject(ticket: Ticket) -> str:
    return f"[Ticket #{ticket.id}] {ticket.email.subject}"


@router.post("/{ticket_id}/send", response_model=SendOut, status_code=201)
def send_ticket_emails(
    ticket_id: int,
    payload: SendIn,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    """Send the reply to the customer and, if chosen, a notice to a department. Then we are done."""
    ticket = get_ticket_or_404(db, ticket_id, agent)
    department = None
    if payload.department_id is not None:
        department = get_department_or_404(db, ticket, payload.department_id)
    if ticket.reply is not None or ticket.status == TicketStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="The emails for this ticket were already sent")

    reply = Reply(
        ticket_id=ticket.id,
        to_email=ticket.email.sender_email,
        subject=f"Re: {ticket.email.subject}",
        body=payload.reply_body,
    )
    db.add(reply)

    notice = None
    if department is not None and payload.department_body is not None:
        notice = Escalation(
            ticket_id=ticket.id,
            department_id=department.id,
            to_email=department.email,
            subject=escalation_subject(ticket),
            body=payload.department_body,
        )
        db.add(notice)

    ticket.status = TicketStatus.COMPLETED
    try:
        db.commit()  # both records and the new status are saved together, or not at all
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="The emails for this ticket were already sent")

    send_email(reply.to_email, reply.subject, reply.body)
    if notice is not None:
        send_email(notice.to_email, notice.subject, notice.body)
    return SendOut(
        ticket_id=ticket.id,
        status=ticket.status,
        reply_sent_to=reply.to_email,
        department_notified=department.name if department else None,
    )


@router.post("/{ticket_id}/reply", response_model=ReplyOut, status_code=201, deprecated=True)
def send_reply(
    ticket_id: int,
    payload: ReplyIn,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    ticket = get_ticket_or_404(db, ticket_id, agent)

    reply = Reply(
        ticket_id=ticket.id,
        to_email=ticket.email.sender_email,
        subject=f"Re: {ticket.email.subject}",
        body=payload.body,
    )
    db.add(reply)
    if ticket.escalation is None:
        ticket.status = TicketStatus.COMPLETED  # nothing else to wait for
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This ticket already has a reply")
    db.refresh(reply)

    send_email(reply.to_email, reply.subject, reply.body)
    return reply


@router.post("/{ticket_id}/escalation-draft", response_model=EscalationDraft)
def create_escalation_draft(
    ticket_id: int,
    choice: DepartmentChoice,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    ticket = get_ticket_or_404(db, ticket_id, agent)
    department = get_department_or_404(db, ticket, choice.department_id)
    try:
        body = draft_escalation(ticket, department)
    except ConnectionError:
        raise HTTPException(status_code=503, detail="AI service (Ollama) is not reachable")
    return EscalationDraft(
        department=department.name,
        to_email=department.email,
        subject=escalation_subject(ticket),
        body=body,
    )


@router.post(
    "/{ticket_id}/escalate", response_model=EscalationOut, status_code=201, deprecated=True
)
def escalate(
    ticket_id: int,
    payload: EscalationIn,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    ticket = get_ticket_or_404(db, ticket_id, agent)
    department = get_department_or_404(db, ticket, payload.department_id)
    if ticket.status == TicketStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Ticket is already completed")

    escalation = Escalation(
        ticket_id=ticket.id,
        department_id=department.id,
        to_email=department.email,
        subject=escalation_subject(ticket),
        body=payload.body,
    )
    db.add(escalation)
    ticket.status = TicketStatus.PENDING  # saved in the SAME commit as the escalation
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This ticket already has an escalation")
    db.refresh(escalation)

    send_email(escalation.to_email, escalation.subject, escalation.body)
    return escalation


@router.post("/{ticket_id}/complete", response_model=TicketStatusOut, deprecated=True)
def complete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    ticket = get_ticket_or_404(db, ticket_id, agent)
    if ticket.status == TicketStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Ticket is already completed")
    ticket.status = TicketStatus.COMPLETED
    db.commit()
    db.refresh(ticket)
    return ticket