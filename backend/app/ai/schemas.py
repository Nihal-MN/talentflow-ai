"""Pydantic schemas for LLM structured outputs.

These models are the contract with the OpenAI Responses API (`text_format=`)
and the validation gate in front of the database: whatever a model returns
must parse into these shapes before any service persists it (see ADR 0002).

Structured-output notes:
* every field is required in the JSON schema; optionality is expressed as
  ``X | None`` (strict mode does not support default values),
* enums are plain literals so both providers validate against identical rules.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

RequirementKind = str  # "must_have" | "preferred"
RequirementCategory = (
    str  # skill | experience | education | certification | domain | location | other
)


class JobRequirementModel(BaseModel):
    """One requirement extracted from a job description."""

    kind: RequirementKind = Field(description='"must_have" or "preferred"')
    category: RequirementCategory = Field(
        description="one of: skill, experience, education, certification, domain, location, other"
    )
    label: str = Field(description="human-readable requirement statement")
    normalized_skill: str | None = Field(
        default=None, description="canonical lowercase skill name when category is 'skill'"
    )
    min_years: float | None = Field(
        default=None, description="minimum years for experience requirements"
    )
    keywords: list[str] = Field(
        default_factory=list, description="2-6 keywords used to find evidence in resumes"
    )


class JobExtractionModel(BaseModel):
    """Structured job description."""

    title: str
    company: str | None = None
    location: str | None = None
    employment_type: str | None = Field(
        default=None, description="full_time | part_time | contract | internship"
    )
    seniority: str | None = Field(
        default=None, description="junior | mid | senior | lead | principal"
    )
    domain: str | None = Field(default=None, description="industry domain, e.g. logistics, fintech")
    summary: str | None = None
    requirements: list[JobRequirementModel]


class ExperienceModel(BaseModel):
    company: str | None = None
    title: str | None = None
    location: str | None = None
    start_date: str | None = Field(default=None, description="ISO date or YYYY-MM, best effort")
    end_date: str | None = Field(default=None, description="ISO date or YYYY-MM; null when current")
    is_current: bool = False
    description: str | None = Field(
        default=None, description="responsibilities/achievements as plain text"
    )


class EducationModel(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class SkillModel(BaseModel):
    name: str = Field(description="skill as written in the resume")
    normalized_name: str = Field(description="canonical lowercase name")
    category: str = Field(
        default="other",
        description=(
            "language | framework | database | cloud | devops | data | testing | "
            "ai | analytics | tool | soft | other"
        ),
    )
    evidence: str | None = Field(default=None, description="source sentence proving the skill")


class CertificationModel(BaseModel):
    name: str
    issuer: str | None = None
    year: int | None = None


class CandidateExtractionModel(BaseModel):
    """Structured resume."""

    full_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = Field(default=None, description="professional headline/title")
    summary: str | None = None
    years_experience: float | None = Field(
        default=None, description="total relevant years, computed from dates"
    )
    linkedin_url: str | None = None
    github_url: str | None = None
    website_url: str | None = None
    experiences: list[ExperienceModel]
    educations: list[EducationModel]
    skills: list[SkillModel]
    certifications: list[CertificationModel]


class ScreeningQuestionModel(BaseModel):
    category: str = Field(description="technical | experience | gap_probe | behavioral")
    question: str
    rationale: str | None = Field(
        default=None, description="why this question matters for this candidate"
    )


class ScreeningQuestionsModel(BaseModel):
    questions: list[ScreeningQuestionModel]
