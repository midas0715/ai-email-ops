from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from ai_email_ops.app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

ROLE_AGENT = "agent"
ROLE_ORG = "org"


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": str(subject_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, expected_role: str) -> int | None:
    """Return the id inside the token, or None if the token is bad, expired, or has the wrong role."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("role") != expected_role:
            return None
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None