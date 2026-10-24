import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai_email_ops.app.db import Base


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    PENDING = "pending"
    COMPLETED = "completed"


class Organization(Base):
    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    agents: Mapped[list["SupportAgent"]] = relationship(back_populates="organization")
    emails: Mapped[list["Email"]] = relationship(back_populates="organization")


class SupportAgent(Base):
    __tablename__ = "support_agent"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id"))
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))  # used by the auth code later
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="agents")
    emails: Mapped[list["Email"]] = relationship(back_populates="assigned_agent")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="agent")


class Email(Base):
    __tablename__ = "email"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id"))
    assigned_agent_id: Mapped[int | None] = mapped_column(ForeignKey("support_agent.id"), nullable=True)
    sender_email: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="emails")
    assigned_agent: Mapped["SupportAgent | None"] = relationship(back_populates="emails")
    ticket: Mapped["Ticket | None"] = relationship(back_populates="email", uselist=False)


class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("email.id"), unique=True)  # one email = one ticket
    agent_id: Mapped[int] = mapped_column(ForeignKey("support_agent.id"))
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.OPEN)
    data: Mapped[dict] = mapped_column(JSONB)  # the agent-validated AI schema
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    email: Mapped["Email"] = relationship(back_populates="ticket")
    agent: Mapped["SupportAgent"] = relationship(back_populates="tickets")
    reply: Mapped["Reply | None"] = relationship(back_populates="ticket", uselist=False)
    escalation: Mapped["Escalation | None"] = relationship(back_populates="ticket", uselist=False)

class Reply(Base):
    __tablename__ = "reply"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("ticket.id"), unique=True)  # one reply per ticket
    to_email: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticket: Mapped["Ticket"] = relationship(back_populates="reply")

class Department(Base):
    __tablename__ = "department"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)  # no two "HR" in one organization

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id"))
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(320))


class Escalation(Base):
    __tablename__ = "escalation"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("ticket.id"), unique=True)  # one escalation per ticket
    department_id: Mapped[int] = mapped_column(ForeignKey("department.id"))
    to_email: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticket: Mapped["Ticket"] = relationship(back_populates="escalation")
    department: Mapped["Department"] = relationship()