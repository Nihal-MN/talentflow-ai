"""Shared test fixtures.

Every test runs hermetically against a throwaway in-memory SQLite database
with the deterministic mock AI providers forced on — no network, no API keys,
no shared state between tests.
"""

from __future__ import annotations

import os
from pathlib import Path

# Must be set before the application modules are imported (CI may legitimately
# override DATABASE_URL to exercise the PostgreSQL path).
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("AI_PROVIDER", "mock")
os.environ["OPENAI_API_KEY"] = ""

import app.models  # noqa: F401  (register all tables)
import pytest
from app.ai.embeddings import HashEmbeddingProvider
from app.ai.mock_provider import MockLLMProvider
from app.api.deps import get_embedding_provider, get_llm_provider
from app.db.base import Base
from app.db.session import get_db as app_get_db
from app.main import app as fastapi_app
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

#: Repository root (backend/tests/conftest.py -> parents[2]).
REPO_ROOT = Path(__file__).resolve().parents[2]


def resume_path(filename: str) -> Path:
    """Absolute path of a committed synthetic demo resume file."""
    return REPO_ROOT / "examples" / "resumes" / filename


@pytest.fixture(scope="session")
def engine():
    """One shared in-memory database for the whole test session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_fks(dbapi_connection, _record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(engine):
    """A clean session per test; all rows are wiped afterwards."""
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    yield session
    session.rollback()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient wired to the test database + mock providers."""

    def _override_db():
        yield db_session

    fastapi_app.dependency_overrides[app_get_db] = _override_db
    fastapi_app.dependency_overrides[get_llm_provider] = MockLLMProvider
    fastapi_app.dependency_overrides[get_embedding_provider] = HashEmbeddingProvider
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


# ── Domain fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def fullstack_job(client) -> dict:
    """The demo Senior Full Stack Engineer job, created through the API."""
    from app.seed.demo_jobs import DEMO_JOBS

    response = client.post(
        "/api/v1/jobs",
        json={
            "title": "Senior Full Stack Engineer",
            "company": "Cedar Freight",
            "jd_text": DEMO_JOBS["senior-full-stack-engineer"]["text"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def amira(client) -> dict:
    """A candidate ingested from the committed synthetic PDF resume."""
    path = resume_path("amira_haddad.resume.pdf")
    response = client.post(
        "/api/v1/candidates/upload",
        files={"file": (path.name, path.read_bytes(), "application/pdf")},
    )
    assert response.status_code == 201, response.text
    return response.json()
