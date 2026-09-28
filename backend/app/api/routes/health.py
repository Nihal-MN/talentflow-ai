"""Health endpoints: liveness probe + full dependency report.

The full report tests the database, reports AI configuration state and entity
counts. Secrets are never included — only whether a key is configured.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import func, select, text

from app import __version__
from app.ai.factory import provider_status
from app.api.deps import DbSession, SettingsDep
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.common import AIHealth, CountsOut, DatabaseHealth, HealthOut

router = APIRouter(tags=["system"])


@router.get("/health/live", summary="Liveness probe")
def liveness() -> dict[str, str]:
    """Cheap liveness check used by Docker healthchecks."""
    return {"status": "ok"}


@router.get("/health", response_model=HealthOut, summary="Full system health")
def health(db: DbSession, settings: SettingsDep) -> HealthOut:
    """Database connectivity/latency, AI configuration, and entity counts."""
    start = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        dialect = db.get_bind().dialect.name
        database = DatabaseHealth(
            status="ok",
            dialect=dialect,
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
        )
    except Exception as exc:
        database = DatabaseHealth(status="error", dialect="unknown", detail=str(exc)[:200])

    counts = CountsOut(
        candidates=db.scalar(select(func.count(Candidate.id))) or 0,
        jobs=db.scalar(select(func.count(Job.id))) or 0,
        open_jobs=db.scalar(select(func.count(Job.id)).where(Job.status == "open")) or 0,
        applications=db.scalar(select(func.count(Application.id))) or 0,
    )
    ai = AIHealth(**provider_status(settings))  # type: ignore[arg-type]

    overall = "ok" if database.status == "ok" and not ai.misconfigured else "degraded"
    return HealthOut(
        status=overall,
        app=settings.app_name,
        version=__version__,
        time=datetime.now(UTC).isoformat(timespec="seconds"),
        database=database,
        ai=ai,
        counts=counts,
    )
