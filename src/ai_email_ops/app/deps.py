from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ai_email_ops.app.db import get_db
from ai_email_ops.app.models import Organization, SupportAgent
from ai_email_ops.app.security import ROLE_AGENT, ROLE_ORG, decode_access_token

agent_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", scheme_name="AgentLogin")
org_scheme = OAuth2PasswordBearer(tokenUrl="/auth/org-login", scheme_name="OrgLogin")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_agent(
    token: str = Depends(agent_scheme), db: Session = Depends(get_db)
) -> SupportAgent:
    """Turns an AGENT token into the logged-in agent, or 401."""
    agent_id = decode_access_token(token, ROLE_AGENT)
    agent = db.get(SupportAgent, agent_id) if agent_id else None
    if agent is None or not agent.is_active:
        raise _unauthorized()
    return agent


def get_current_org(
    token: str = Depends(org_scheme), db: Session = Depends(get_db)
) -> Organization:
    """Turns an ORGANIZATION (CEO) token into the logged-in organization, or 401."""
    org_id = decode_access_token(token, ROLE_ORG)
    org = db.get(Organization, org_id) if org_id else None
    if org is None:
        raise _unauthorized()
    return org