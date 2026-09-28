"""Note, tag and screening-question schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="Recruiter", max_length=120)
    job_id: int | None = None


class NoteOut(BaseModel):
    id: int
    candidate_id: int
    job_id: int | None
    author: str
    body: str
    created_at: datetime


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    color: str = Field(default="slate", max_length=20)


class TagOut(BaseModel):
    id: int
    name: str
    color: str


class TagUsageOut(TagOut):
    usage_count: int


class ScreeningQuestionOut(BaseModel):
    id: int
    application_id: int
    category: str
    question: str
    rationale: str | None
    source: str
    order_index: int
    created_at: datetime


class ScreeningRequest(BaseModel):
    """Body for generating a screening-question set (kept for future options)."""

    regenerate: bool = True


class ScreeningListItem(BaseModel):
    """One row of the Screening Questions page: an application + its set."""

    application_id: int
    candidate_id: int
    candidate_name: str
    job_id: int
    job_title: str
    stage: str
    source: str
    question_count: int
    created_at: datetime | None
