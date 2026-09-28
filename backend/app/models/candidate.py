"""Candidate domain models — the validated, structured talent profile.

Everything stored here was produced by the resume ingestion pipeline: document
extraction → structured LLM extraction → Pydantic validation → normalization.
Raw, unvalidated model output is never persisted as structured truth; the
original document text is kept separately (``resume_text``) purely as an
evidence source and is treated as untrusted content.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.tag import Tag, candidate_tags

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.note import CandidateNote


class Candidate(Base, TimestampMixin):
    """A person in the talent pool, with a validated structured profile."""

    __tablename__ = "candidates"
    __table_args__ = (Index("ix_candidates_full_name", "full_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(200))
    headline: Mapped[str | None] = mapped_column(String(300))
    summary: Mapped[str | None] = mapped_column(Text)
    years_experience: Mapped[float | None] = mapped_column(Float)

    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    website_url: Mapped[str | None] = mapped_column(String(500))

    # Provenance of the source document (file stored under UPLOAD_DIR).
    resume_filename: Mapped[str | None] = mapped_column(String(300))
    resume_path: Mapped[str | None] = mapped_column(String(1000))
    # Raw source text — an evidence source, never the structured truth.
    resume_text: Mapped[str | None] = mapped_column(Text)

    # Transparency: how this profile was produced ("openai" | "mock" | "manual").
    extraction_method: Mapped[str] = mapped_column(String(30), default="mock", nullable=False)
    extraction_model: Mapped[str | None] = mapped_column(String(120))

    experiences: Mapped[list[CandidateExperience]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
        order_by="CandidateExperience.order_index",
    )
    educations: Mapped[list[CandidateEducation]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
        order_by="CandidateEducation.order_index",
    )
    skills: Mapped[list[CandidateSkill]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
        order_by="CandidateSkill.normalized_name",
    )
    certifications: Mapped[list[CandidateCertification]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
        order_by="CandidateCertification.name",
    )
    tags: Mapped[list[Tag]] = relationship(secondary=candidate_tags, order_by="Tag.name")
    applications: Mapped[list[Application]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
        order_by="Application.created_at",
    )
    notes: Mapped[list[CandidateNote]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Candidate id={self.id} name={self.full_name!r}>"


class CandidateExperience(Base, TimestampMixin):
    """One role held by a candidate."""

    __tablename__ = "candidate_experiences"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    company: Mapped[str | None] = mapped_column(String(200))
    title: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(200))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="experiences")


class CandidateEducation(Base, TimestampMixin):
    """One education entry."""

    __tablename__ = "candidate_educations"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    institution: Mapped[str | None] = mapped_column(String(300))
    degree: Mapped[str | None] = mapped_column(String(200))
    field_of_study: Mapped[str | None] = mapped_column(String(200))
    start_year: Mapped[int | None] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="educations")


class CandidateSkill(Base, TimestampMixin):
    """A normalized, deduplicated skill with evidence from the resume."""

    __tablename__ = "candidate_skills"
    __table_args__ = (UniqueConstraint("candidate_id", "normalized_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)  # as written in the resume
    normalized_name: Mapped[str] = mapped_column(String(120), nullable=False)  # canonical form
    category: Mapped[str] = mapped_column(String(40), default="other", nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)  # snippet proving the skill

    candidate: Mapped[Candidate] = relationship(back_populates="skills")


class CandidateCertification(Base, TimestampMixin):
    """A certification or license."""

    __tablename__ = "candidate_certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(200))
    year: Mapped[int | None] = mapped_column(Integer)

    candidate: Mapped[Candidate] = relationship(back_populates="certifications")
