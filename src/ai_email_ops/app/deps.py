from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ai_email_ops.app.db import get_db
from ai_email_ops.app.models import SupportAgent
from ai_email_ops.app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_agent(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> SupportAgent:
    """Used as a dependency: turns the token into the logged-in agent, or returns 401."""
    agent_id = decode_access_token(token)
    agent = db.get(SupportAgent, agent_id) if agent_id else None
    if agent is None or not agent.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return agent