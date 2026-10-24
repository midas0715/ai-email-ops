from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_email_ops.app.db import get_db
from ai_email_ops.app.models import SupportAgent
from ai_email_ops.app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # the form field is called "username", but we use it for the agent's email
    agent = db.scalars(select(SupportAgent).where(SupportAgent.email == form.username)).first()
    if agent is None or not agent.is_active or not verify_password(form.password, agent.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return TokenOut(access_token=create_access_token(agent.id))