from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_email_ops.app.db import get_db
from ai_email_ops.app.models import Organization, SupportAgent
from ai_email_ops.app.security import (
    ROLE_AGENT,
    ROLE_ORG,
    create_access_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Agent login. The form field is called 'username', but we use it for the email."""
    agent = db.scalars(
        select(SupportAgent).where(SupportAgent.email == form.username.lower())
    ).first()
    if agent is None or not agent.is_active or not verify_password(form.password, agent.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return TokenOut(access_token=create_access_token(agent.id, ROLE_AGENT))


@router.post("/org-login", response_model=TokenOut)
def org_login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """CEO login with the organization's email and password."""
    org = db.scalars(
        select(Organization).where(Organization.email == form.username.lower())
    ).first()
    if org is None or org.hashed_password is None or not verify_password(form.password, org.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return TokenOut(access_token=create_access_token(org.id, ROLE_ORG))