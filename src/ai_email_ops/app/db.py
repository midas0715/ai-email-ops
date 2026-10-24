from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from ai_email_ops.app.config import settings

# The engine is the connection pool to Postgres
engine = create_engine(settings.database_url)

# A session is one "conversation" with the DB (like opening a notebook, writing, saving)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Every model inherits from this so SQLAlchemy can track all tables."""


def get_db():
    """FastAPI dependency: opens a session per request, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()