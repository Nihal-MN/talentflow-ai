"""Application & pipeline endpoints: add to pipeline, move stages, board,
recent activity."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.serializers import application_out
from app.schemas.application import (
    ActivityOut,
    ApplicationCreate,
    ApplicationOut,
    StageMove,
)
from app.services import pipeline

router = APIRouter(prefix="/applications", tags=["pipeline"])


@router.get("", response_model=list[ApplicationOut], summary="List applications")
def list_applications(
    db: DbSession,
    job_id: int | None = None,
    candidate_id: int | None = None,
    stage: str | None = None,
    limit: int = 200,
) -> list[ApplicationOut]:
    applications = pipeline.list_applications(
        db, job_id=job_id, candidate_id=candidate_id, stage=stage, limit=limit
    )
    return [application_out(application) for application in applications]


@router.get("/board", response_model=dict[str, list[ApplicationOut]], summary="Pipeline board")
def get_board(db: DbSession, job_id: int | None = None) -> dict[str, list[ApplicationOut]]:
    board = pipeline.get_board(db, job_id=job_id)
    return {
        stage: [application_out(application) for application in applications]
        for stage, applications in board.items()
    }


@router.get("/activity", response_model=list[ActivityOut], summary="Recent pipeline activity")
def recent_activity(db: DbSession, limit: int = 12) -> list[ActivityOut]:
    events = pipeline.recent_activity(db, limit=limit)
    return [
        ActivityOut(
            application_id=event.application_id,
            candidate_id=event.application.candidate_id if event.application else 0,
            candidate_name=event.application.candidate.full_name
            if event.application and event.application.candidate
            else "",
            job_id=event.application.job_id if event.application else 0,
            job_title=event.application.job.title
            if event.application and event.application.job
            else "",
            from_stage=event.from_stage,
            to_stage=event.to_stage,
            note=event.note,
            at=event.created_at,
        )
        for event in events
    ]


@router.post("", response_model=ApplicationOut, status_code=201, summary="Add candidate to a job")
def create_application(payload: ApplicationCreate, db: DbSession) -> ApplicationOut:
    application = pipeline.create_application(
        db,
        candidate_id=payload.candidate_id,
        job_id=payload.job_id,
        note=payload.note,
    )
    application = pipeline.get_application(db, application.id)
    return application_out(application, include_events=True)


@router.get("/{application_id}", response_model=ApplicationOut, summary="Application detail")
def get_application(application_id: int, db: DbSession) -> ApplicationOut:
    application = pipeline.get_application(db, application_id)
    return application_out(application, include_events=True)


@router.patch("/{application_id}/stage", response_model=ApplicationOut, summary="Move stage")
def move_stage(application_id: int, payload: StageMove, db: DbSession) -> ApplicationOut:
    pipeline.move_stage(db, application_id, to_stage=payload.to_stage, note=payload.note)
    application = pipeline.get_application(db, application_id)
    return application_out(application, include_events=True)


@router.delete("/{application_id}", status_code=204, summary="Delete an application")
def delete_application(application_id: int, db: DbSession) -> None:
    pipeline.delete_application(db, application_id)
