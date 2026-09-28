"""AI provider interfaces and value objects.

The application never talks to an LLM SDK directly — it depends on the
``LLMProvider`` and ``EmbeddingProvider`` protocols defined here. Two real
implementations exist: a current-OpenAI one and a deterministic offline mock
(see docs/adr/0002). Value objects are plain dataclasses so services and tests
do not depend on any provider's wire format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Protocol, runtime_checkable

# ── Extraction value objects ─────────────────────────────────────────────────


@dataclass(slots=True)
class ExtractedRequirement:
    """One evaluable requirement parsed from a job description."""

    kind: str  # "must_have" | "preferred"
    category: str  # skill | experience | education | certification | domain | location | other
    label: str  # human-readable statement, e.g. "5+ years of backend experience"
    normalized_skill: str | None = None  # canonical skill name when category == "skill"
    min_years: float | None = None  # for experience requirements
    keywords: list[str] = field(default_factory=list)  # keywords for evidence search


@dataclass(slots=True)
class ExtractedJob:
    """Structured job description."""

    title: str
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None  # full_time | part_time | contract | internship
    seniority: str | None = None  # junior | mid | senior | lead | principal
    domain: str | None = None  # e.g. "logistics", "fintech"
    summary: str | None = None
    requirements: list[ExtractedRequirement] = field(default_factory=list)


@dataclass(slots=True)
class ExtractedExperience:
    company: str | None = None
    title: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description: str | None = None


@dataclass(slots=True)
class ExtractedEducation:
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None


@dataclass(slots=True)
class ExtractedSkill:
    name: str  # as found in the document
    normalized_name: str  # canonical name
    category: str = "other"  # language | framework | database | cloud | tool | soft | other
    evidence: str | None = None  # source snippet proving the skill


@dataclass(slots=True)
class ExtractedCertification:
    name: str
    issuer: str | None = None
    year: int | None = None


@dataclass(slots=True)
class ExtractedCandidate:
    """Structured resume."""

    full_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    summary: str | None = None
    years_experience: float | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    website_url: str | None = None
    experiences: list[ExtractedExperience] = field(default_factory=list)
    educations: list[ExtractedEducation] = field(default_factory=list)
    skills: list[ExtractedSkill] = field(default_factory=list)
    certifications: list[ExtractedCertification] = field(default_factory=list)


@dataclass(slots=True)
class ScreeningQuestionDraft:
    """One generated screening question."""

    category: str  # technical | experience | gap_probe | behavioral
    question: str
    rationale: str | None = None


# ── Provider protocols ───────────────────────────────────────────────────────


@runtime_checkable
class LLMProvider(Protocol):
    """Text-in / validated-structures-out provider."""

    #: Machine-readable provider name, e.g. "mock" or "openai".
    name: str
    #: Model identifier, e.g. "deterministic-rules-v1" or "gpt-5.6-terra".
    model: str

    def extract_job(self, jd_text: str) -> ExtractedJob:
        """Parse a job description into a structured job + requirements."""
        ...

    def extract_candidate(
        self, resume_text: str, *, source_filename: str | None = None
    ) -> ExtractedCandidate:
        """Parse resume text into a structured candidate profile."""
        ...

    def generate_screening_questions(
        self,
        *,
        job_title: str,
        candidate_name: str,
        years_experience: float | None,
        matched_skills: list[str],
        missing_skills: list[str],
        seniority: str | None,
    ) -> list[ScreeningQuestionDraft]:
        """Generate candidate-specific screening questions."""
        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Batch text → vectors provider."""

    #: Machine-readable provider name, e.g. "mock" or "openai".
    name: str
    #: Model identifier recorded alongside stored vectors.
    model: str
    #: Vector dimension (must match the storage column).
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, preserving order."""
        ...
