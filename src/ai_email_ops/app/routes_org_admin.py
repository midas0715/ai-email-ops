from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_email_ops.app.assignment import pick_random_agent
from ai_email_ops.app.db import get_db
from ai_email_ops.app.deps import get_current_org
from ai_email_ops.app.models import (
    Department,
    Email,
    Escalation,
    Organization,
    SupportAgent,
    Ticket,
    TicketStatus,
)
from ai_email_ops.app.security import hash_password
from ai_email_ops.app.security import generate_api_key, hash_api_key, hash_password
from ai_email_ops.app.schemas import Category

router = APIRouter(prefix="/orgs/me", tags=["organization admin"])


class AgentCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class AgentOut(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool

    model_config = {"from_attributes": True}


class AgentRemovedOut(BaseModel):
    agent_id: int
    reassigned_emails: int


class DepartmentIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    categories: list[Category] = []

class DepartmentOut(BaseModel):
    id: int
    name: str
    email: str
    categories: list[str]
    model_config = {"from_attributes": True}

class ApiKeyOut(BaseModel):
    api_key: str
    hint: str
    note: str = "Copy this key now. It is shown only once."

def get_agent_or_404(db: Session, org: Organization, agent_id: int) -> SupportAgent:
    agent = db.get(SupportAgent, agent_id)
    # an agent of ANOTHER organization looks exactly like a missing one
    if agent is None or agent.organization_id != org.id:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


def get_department_or_404(db: Session, org: Organization, department_id: int) -> Department:
    department = db.get(Department, department_id)
    if department is None or department.organization_id != org.id:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


# ---------- agents ----------


@router.post("/agents", response_model=AgentOut, status_code=201)
def create_agent(
    payload: AgentCreateIn,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    agent = SupportAgent(
        organization_id=org.id,
        name=payload.name.strip(),
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
    )
    db.add(agent)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An agent with this email already exists")
    db.refresh(agent)
    return agent


@router.get("/agents", response_model=list[AgentOut])
def list_agents(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    stmt = select(SupportAgent).where(SupportAgent.organization_id == org.id).order_by(SupportAgent.id)
    return db.scalars(stmt).all()


@router.delete("/agents/{agent_id}", response_model=AgentRemovedOut)
def remove_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    agent = get_agent_or_404(db, org, agent_id)
    if not agent.is_active:
        raise HTTPException(status_code=409, detail="Agent is already removed")

    unfinished = db.scalar(
        select(func.count())
        .select_from(Ticket)
        .where(Ticket.agent_id == agent.id, Ticket.status != TicketStatus.COMPLETED)
    )
    if unfinished:
        raise HTTPException(
            status_code=409,
            detail=f"Agent has {unfinished} unfinished ticket(s). Finish or complete them first.",
        )

    # emails given to this agent that nobody has started a ticket for
    untouched = db.scalars(
        select(Email).where(Email.assigned_agent_id == agent.id, ~Email.ticket.has())
    ).all()
    if untouched and pick_random_agent(db, org.id, exclude_agent_id=agent.id) is None:
        raise HTTPException(
            status_code=409,
            detail="This agent has emails waiting and there is no other active agent. Add one first.",
        )

    for email in untouched:
        email.assigned_agent_id = pick_random_agent(db, org.id, exclude_agent_id=agent.id).id
    agent.is_active = False
    db.commit()  # the hand-off and the deactivation are saved together or not at all
    return AgentRemovedOut(agent_id=agent.id, reassigned_emails=len(untouched))


# ---------- departments ----------


@router.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(
    payload: DepartmentIn,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    department = Department(
        organization_id=org.id,
        name=payload.name.strip(),
        email=payload.email.lower(),
        categories=sorted({c.value for c in payload.categories}),  # duplicates removed
    )
    db.add(department)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A department with this name already exists")
    db.refresh(department)
    return department


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    stmt = select(Department).where(Department.organization_id == org.id).order_by(Department.id)
    return db.scalars(stmt).all()


@router.delete("/departments/{department_id}", status_code=204)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    department = get_department_or_404(db, org, department_id)
    used = db.scalar(
        select(func.count()).select_from(Escalation).where(Escalation.department_id == department.id)
    )
    if used:
        raise HTTPException(
            status_code=409, detail="This department is used by existing escalations and cannot be deleted"
        )
    db.delete(department)
    db.commit()

class DepartmentCategoriesIn(BaseModel):
    categories: list[Category]


@router.put("/departments/{department_id}/categories", response_model=DepartmentOut)
def set_department_categories(
    department_id: int,
    payload: DepartmentCategoriesIn,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    department = get_department_or_404(db, org, department_id)
    department.categories = sorted({c.value for c in payload.categories})
    db.commit()
    db.refresh(department)
    return department

# ---------- API key for incoming emails ----------


@router.post("/api-key", response_model=ApiKeyOut, status_code=201)
def create_api_key(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    """Create a key, or replace the old one. The old key stops working immediately."""
    key = generate_api_key()
    org.api_key_hash = hash_api_key(key)  # only the hash is stored
    org.api_key_hint = key[-4:]
    db.commit()
    return ApiKeyOut(api_key=key, hint=org.api_key_hint)


@router.delete("/api-key", status_code=204)
def revoke_api_key(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    org.api_key_hash = None
    org.api_key_hint = None
    db.commit()