"""Database engine and session management (dialect-aware).

The runtime path is PostgreSQL + pgvector (Docker Compose). When
``DATABASE_URL`` is empty the app falls back to a local SQLite file, so
development and tests need no external services. See docs/adr/0001 and
docs/adr/0004.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings


def _prepare_sqlite_path(url: str) -> None:
    """Make sure the parent directory for a file-based SQLite DB exists."""
    if url.startswith("sqlite:///"):
        path = url.removeprefix("sqlite:///")
        if path and path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)


def build_engine(url: str | None = None) -> Engine:
    """Create an engine for ``url`` (defaults to the configured database)."""
    effective = (url or get_settings().sqlalchemy_url).strip()
    kwargs: dict = {"pool_pre_ping": True}

    if effective.startswith("sqlite"):
        _prepare_sqlite_path(effective)
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in effective:
            # One shared in-memory database across the whole test process.
            kwargs["poolclass"] = StaticPool

    engine = create_engine(effective, **kwargs)

    if effective.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _enable_sqlite_fks(dbapi_connection, _record) -> None:
            # SQLite ignores ON DELETE CASCADE unless foreign keys are enabled
            # per connection — keep parity with PostgreSQL behavior.
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


# Note: pgvector values are sent/received as text by the EmbeddingVector type
# (with an explicit ::vector cast in similarity SQL), so no psycopg adapter
# registration is required — see app/models/embedding.py.


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: yield a session, always close it."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
