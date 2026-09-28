"""Application / pipeline schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.candidate import CandidateBrief
from app.schemas.job import JobBrief


class StageEventOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    from_stage: str | None
    to_stage: str
    note: str | None
    created_at: datetime


class ApplicationCreate(BaseModel):
    candidate_id: int
    job_id: int
    note: str | None = Field(default=None, max_length=2000)


class StageMove(BaseModel):
    to_stage: str
    note: str | None = Field(default=None, max_length=2000)


class ApplicationOut(BaseModel):
    """Composed in the serializer layer (embeds candidate + job briefly)."""

    id: int
    candidate_id: int
    job_id: int
    stage: str
    created_at: datetime
    updated_at: datetime
    candidate: CandidateBrief
    job: JobBrief
    screening_questions_count: int = 0
    stage_events: list[StageEventOut] = []


class ActivityOut(BaseModel):
    """One pipeline activity entry (dashboard feed)."""

    application_id: int
    candidate_id: int
    candidate_name: str
    job_id: int
    job_title: str
    from_stage: str | None
    to_stage: str
    note: str | None
    at: datetime
