"""Applications and pipeline services.

Adding a candidate to a job, moving stages (with an audit trail of
``PipelineStageEvent`` rows) and reading the pipeline board. Stage values are
validated here against the ``PipelineStage`` enum.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFoundError, ValidationAppError
from app.models.application import (
    STAGE_ORDER,
    Application,
    PipelineStage,
    PipelineStageEvent,
)
from app.models.candidate import Candidate
from app.models.job import Job

logger = logging.getLogger("talentflow.pipeline")

VALID_STAGES = {stage.value for stage in PipelineStage}

_APPLICATION_LOADERS = (
    selectinload(Application.candidate),
    selectinload(Application.job),
)


def create_application(
    db: Session,
    *,
    candidate_id: int,
    job_id: int,
    stage: str = PipelineStage.NEW.value,
    note: str | None = None,
) -> Application:
    """Add a candidate to a job's pipeline (idempotent for an existing pair)."""
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise NotFoundError(f"Candidate {candidate_id} does not exist.")
    job = db.get(Job, job_id)
    if job is None:
        raise NotFoundError(f"Job {job_id} does not exist.")
    if stage not in VALID_STAGES:
        raise ValidationAppError(f"Unknown pipeline stage '{stage}'.")

    existing = db.execute(
        select(Application).where(
            Application.candidate_id == candidate_id, Application.job_id == job_id
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing  # idempotent: already in this pipeline

    application = Application(candidate_id=candidate_id, job_id=job_id, stage=stage)
    db.add(application)
    db.flush()
    db.add(
        PipelineStageEvent(
            application_id=application.id,
            from_stage=None,
            to_stage=stage,
            note=note or "Added to pipeline",
        )
    )
    db.commit()
    db.refresh(application)
    logger.info(
        "application created",
        extra={"application_id": application.id, "candidate_id": candidate_id, "job_id": job_id},
    )
    return application


def move_stage(
    db: Session, application_id: int, *, to_stage: str, note: str | None = None
) -> Application:
    """Move an application to a new stage and record the transition."""
    if to_stage not in VALID_STAGES:
        raise ValidationAppError(
            f"Unknown pipeline stage '{to_stage}'. Valid stages: {', '.join(sorted(VALID_STAGES))}."
        )
    application = get_application(db, application_id)
    if application.stage == to_stage:
        return application  # no-op; no duplicate event

    db.add(
        PipelineStageEvent(
            application_id=application.id,
            from_stage=application.stage,
            to_stage=to_stage,
            note=(note or "").strip() or None,
        )
    )
    previous = application.stage
    application.stage = to_stage
    db.commit()
    db.refresh(application)
    logger.info(
        "stage moved",
        extra={
            "application_id": application.id,
            "from_stage": previous,
            "to_stage": to_stage,
        },
    )
    return application


def get_application(db: Session, application_id: int) -> Application:
    """Fetch one application with candidate + job loaded."""
    application = db.execute(
        select(Application)
        .where(Application.id == application_id)
        .options(*_APPLICATION_LOADERS, selectinload(Application.screening_questions))
    ).scalar_one_or_none()
    if application is None:
        raise NotFoundError(f"Application {application_id} does not exist.")
    return application


def list_applications(
    db: Session,
    *,
    job_id: int | None = None,
    candidate_id: int | None = None,
    stage: str | None = None,
    limit: int = 200,
) -> list[Application]:
    """List applications with candidate + job loaded."""
    statement = (
        select(Application)
        .options(*_APPLICATION_LOADERS)
        .order_by(Application.updated_at.desc(), Application.id.desc())
        .limit(max(1, min(limit, 500)))
    )
    if job_id is not None:
        statement = statement.where(Application.job_id == job_id)
    if candidate_id is not None:
        statement = statement.where(Application.candidate_id == candidate_id)
    if stage is not None:
        statement = statement.where(Application.stage == stage)
    return list(db.execute(statement).scalars())


def get_board(db: Session, *, job_id: int | None = None) -> dict[str, list[Application]]:
    """Applications grouped by stage (all stages present, even when empty)."""
    board: dict[str, list[Application]] = {stage.value: [] for stage in PipelineStage}
    for application in list_applications(db, job_id=job_id, limit=500):
        board.setdefault(application.stage, []).append(application)
    for applications in board.values():
        applications.sort(key=lambda item: item.updated_at or item.created_at, reverse=True)
    return board


def delete_application(db: Session, application_id: int) -> None:
    """Remove an application (cascades its events + screening questions)."""
    application = get_application(db, application_id)
    db.delete(application)
    db.commit()
    logger.info("application deleted", extra={"application_id": application_id})


def recent_activity(db: Session, *, limit: int = 12) -> list[PipelineStageEvent]:
    """Most recent stage transitions, for the dashboard activity feed."""
    statement = (
        select(PipelineStageEvent)
        .options(
            selectinload(PipelineStageEvent.application).selectinload(Application.candidate),
            selectinload(PipelineStageEvent.application).selectinload(Application.job),
        )
        .order_by(PipelineStageEvent.created_at.desc(), PipelineStageEvent.id.desc())
        .limit(max(1, min(limit, 50)))
    )
    return list(db.execute(statement).scalars())


__all__ = [
    "STAGE_ORDER",
    "create_application",
    "delete_application",
    "get_application",
    "get_board",
    "list_applications",
    "move_stage",
    "recent_activity",
]
