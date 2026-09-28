"""Job domain models: postings and their evaluable requirements."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.application import Application


class Job(Base, TimestampMixin):
    """A job posting with structured requirements extracted from its JD."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    employment_type: Mapped[str] = mapped_column(String(40), default="full_time", nullable=False)
    seniority: Mapped[str | None] = mapped_column(
        String(40)
    )  # junior | mid | senior | lead | principal
    domain: Mapped[str | None] = mapped_column(String(80))  # e.g. "logistics", "fintech"
    status: Mapped[str] = mapped_column(
        String(20), default="open", nullable=False
    )  # open | paused | closed

    # The original JD text — an evidence source, treated as untrusted content.
    description_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(
        String(20), default="manual", nullable=False
    )  # manual | upload

    # Transparency: how requirements were extracted ("openai" | "mock" | "manual").
    extraction_method: Mapped[str] = mapped_column(String(30), default="mock", nullable=False)
    extraction_model: Mapped[str | None] = mapped_column(String(120))

    requirements: Mapped[list[JobRequirement]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="JobRequirement.order_index",
    )
    applications: Mapped[list[Application]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Job id={self.id} title={self.title!r} status={self.status}>"


class JobRequirement(Base, TimestampMixin):
    """One evaluable requirement, marked as must-have or preferred.

    ``category`` drives how the matching engine evaluates it:
    skill | experience | education | certification | domain | location | other.
    """

    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )

    kind: Mapped[str] = mapped_column(
        String(20), default="must_have", nullable=False
    )  # must_have | preferred
    category: Mapped[str] = mapped_column(String(40), default="other", nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)  # human-readable statement
    normalized_skill: Mapped[str | None] = mapped_column(
        String(120)
    )  # canonical skill when applicable
    min_years: Mapped[float | None] = mapped_column(Float)  # for experience requirements
    keywords: Mapped[str | None] = mapped_column(String(500))  # comma-joined, for evidence search
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    job: Mapped[Job] = relationship(back_populates="requirements")
