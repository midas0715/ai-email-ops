from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_email_ops.app.db import get_db
from ai_email_ops.app.deps import get_current_org
from ai_email_ops.app.models import Organization
from ai_email_ops.app.security import hash_password

router = APIRouter(prefix="/orgs", tags=["organizations"])


class OrgRegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)  # bcrypt only reads the first 72 bytes


class OrgOut(BaseModel):
    id: int
    name: str
    email: str | None

    model_config = {"from_attributes": True}


@router.post("/register", response_model=OrgOut, status_code=201)
def register_org(payload: OrgRegisterIn, db: Session = Depends(get_db)):
    org = Organization(
        name=payload.name.strip(),
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
    )
    db.add(org)
    try:
        db.commit()  # the unique constraints on name and email are the real guard
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An organization with this name or email already exists")
    db.refresh(org)
    return org


@router.get("/me", response_model=OrgOut)
def my_org(org: Organization = Depends(get_current_org)):
    return org