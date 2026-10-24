import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from ai_email_ops.app import models  # noqa: F401  (so Base knows every table)
from ai_email_ops.app.config import settings
from ai_email_ops.app.db import Base, get_db
from ai_email_ops.app.main import app
from ai_email_ops.app.models import Department, Email, Organization, SupportAgent
from ai_email_ops.app.security import pwd_context

# Same server as the real DB, but always the database called emailops_test
TEST_DB_URL = make_url(settings.database_url).set(database="emailops_test")
test_engine = create_engine(TEST_DB_URL)
TestSession = sessionmaker(bind=test_engine, autoflush=False)

PASSWORD = "password123"
PASSWORD_HASH = pwd_context.hash(PASSWORD)  # hashing is slow on purpose, so do it once


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Once per test run: build all tables fresh in the test database."""
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)


@pytest.fixture(autouse=True)
def empty_tables():
    """Before every test: wipe all rows, so tests can't affect each other."""
    with test_engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE organization, support_agent, email, ticket, reply, "
                "department, escalation RESTART IDENTITY CASCADE"
            )
        )


@pytest.fixture
def db():
    with TestSession() as session:
        yield session


@pytest.fixture
def client():
    """A fake browser whose app uses the test database instead of the real one."""

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def org(db):
    organization = Organization(name="Test Org")
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


@pytest.fixture
def other_org(db):
    organization = Organization(name="Other Org")
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


@pytest.fixture
def make_agent(db, org):
    """Factory: make_agent("asha") creates an agent. All agents use PASSWORD."""

    def _make(name, is_active=True, organization=None):
        agent = SupportAgent(
            organization_id=(organization or org).id,
            name=name,
            email=f"{name}@test.test",
            hashed_password=PASSWORD_HASH,
            is_active=is_active,
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    return _make


@pytest.fixture
def make_email(db, org):
    """Factory: make_email(agent=asha) creates an email already assigned to asha."""

    def _make(agent=None):
        email = Email(
            organization_id=org.id,
            assigned_agent_id=agent.id if agent else None,
            sender_email="customer@example.com",
            subject="Refund request",
            body="I was charged twice for my order.",
        )
        db.add(email)
        db.commit()
        db.refresh(email)
        return email

    return _make


@pytest.fixture
def department(db, org):
    dept = Department(organization_id=org.id, name="Accounting", email="accounting@test.test")
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@pytest.fixture
def login(client):
    """login(agent) returns the Authorization header for that agent."""

    def _login(agent):
        response = client.post(
            "/auth/login", data={"username": agent.email, "password": PASSWORD}
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login


@pytest.fixture
def draft():
    return {
        "summary": "Customer was charged twice.",
        "category": "billing",
        "priority": "high",
        "sentiment": "neutral",
        "requested_action": "Refund the duplicate charge",
    }


@pytest.fixture
def make_ticket(client, login, draft):
    """make_ticket(agent, email) saves a ticket through the real API and returns its id."""

    def _make(agent, email):
        response = client.post(f"/emails/{email.id}/ticket", json=draft, headers=login(agent))
        assert response.status_code == 201, response.text
        return response.json()["id"]

    return _make

@pytest.fixture(autouse=True)
def fake_cache(monkeypatch):
    """Every test gets an in-memory dictionary instead of the real Redis."""
    store = {}
    monkeypatch.setattr("ai_email_ops.app.routes_emails.cache_get", lambda key: store.get(key))
    monkeypatch.setattr(
        "ai_email_ops.app.routes_emails.cache_set",
        lambda key, value, ttl_seconds: store.__setitem__(key, value),
    )
    monkeypatch.setattr(
        "ai_email_ops.app.routes_emails.cache_delete", lambda key: store.pop(key, None)
    )
    return store