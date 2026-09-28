"""Candidate schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.misc import NoteOut, TagOut


class ExperienceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str | None
    title: str | None
    location: str | None
    start_date: date | None
    end_date: date | None
    is_current: bool
    description: str | None


class EducationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institution: str | None
    degree: str | None
    field_of_study: str | None
    start_year: int | None
    end_year: int | None


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    normalized_name: str
    category: str
    evidence: str | None


class CertificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    issuer: str | None
    year: int | None


class ApplicationBriefOut(BaseModel):
    """A candidate's application, viewed from the candidate side."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    job_title: str
    stage: str
    updated_at: datetime


class CandidateBrief(BaseModel):
    """Compact candidate view embedded in application/match payloads."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    headline: str | None
    location: str | None
    years_experience: float | None


class CandidateListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    headline: str | None
    location: str | None
    years_experience: float | None
    extraction_method: str
    created_at: datetime
    skills: list[str]
    applications_count: int


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str | None
    phone: str | None
    location: str | None
    headline: str | None
    summary: str | None
    years_experience: float | None
    linkedin_url: str | None
    github_url: str | None
    website_url: str | None
    resume_filename: str | None
    resume_text: str | None
    extraction_method: str
    extraction_model: str | None
    created_at: datetime
    experiences: list[ExperienceOut]
    educations: list[EducationOut]
    skills: list[SkillOut]
    certifications: list[CertificationOut]
    applications: list[ApplicationBriefOut]
    notes: list[NoteOut]
    tags: list[TagOut]
