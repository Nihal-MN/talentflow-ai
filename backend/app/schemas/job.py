"""Job schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RequirementOut(BaseModel):
    """Built by the serializer layer (keywords split from storage)."""

    id: int
    kind: str
    category: str
    label: str
    normalized_skill: str | None
    min_years: float | None
    keywords: list[str]
    order_index: int


class JobBrief(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    company: str
    location: str | None
    status: str
    seniority: str | None
    employment_type: str
    domain: str | None


class JobCreate(BaseModel):
    """Create a job by pasting a JD. The title may be inferred from the text."""

    title: str | None = Field(default=None, max_length=200)
    company: str = Field(default="", max_length=200)
    location: str | None = Field(default=None, max_length=200)
    employment_type: str | None = Field(default=None, max_length=40)
    jd_text: str = Field(min_length=30, description="Full job description text")


class JobUpdate(BaseModel):
    status: str | None = None
    title: str | None = Field(default=None, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)


class JobListItem(BaseModel):
    id: int
    title: str
    company: str
    location: str | None
    status: str
    seniority: str | None
    employment_type: str
    domain: str | None
    extraction_method: str
    created_at: datetime
    must_have_count: int
    preferred_count: int
    applications_count: int


class JobApplicationBriefOut(BaseModel):
    """An application viewed from the job side."""

    id: int
    candidate_id: int
    candidate_name: str
    candidate_headline: str | None
    stage: str
    updated_at: datetime


class JobOut(JobListItem):
    source: str
    extraction_model: str | None
    description_text: str
    requirements: list[RequirementOut]
    applications: list[JobApplicationBriefOut]
