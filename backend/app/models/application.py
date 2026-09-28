"""Applications and the hiring pipeline.

`Application` links a candidate to a job and carries the current stage.
`PipelineStageEvent` records every transition — the audit trail behind the
Pipeline board and the dashboard activity feed. Stage values are stored as
plain uppercase strings (portable across SQLite/PostgreSQL; validated in the
service layer against `PipelineStage`).
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.job import Job
    from app.models.screening import ScreeningQuestion


class PipelineStage(enum.StrEnum):
    """The stages a candidate moves through for a given job."""

    NEW = "NEW"
    SCREENING = "SCREENING"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    HIRED = "HIRED"
    REJECTED = "REJECTED"


#: Display/logical order of the pipeline (REJECTED is off-board).
STAGE_ORDER: tuple[PipelineStage, ...] = (
    PipelineStage.NEW,
    PipelineStage.SCREENING,
    PipelineStage.SHORTLISTED,
    PipelineStage.INTERVIEW,
    PipelineStage.OFFER,
    PipelineStage.HIRED,
)

ACTIVE_STAGES: tuple[PipelineStage, ...] = STAGE_ORDER


class Application(Base, TimestampMixin):
    """A candidate's candidacy for one job, with its current stage."""

    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    stage: Mapped[str] = mapped_column(String(20), default=PipelineStage.NEW.value, nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="applications")
    job: Mapped[Job] = relationship(back_populates="applications")
    stage_events: Mapped[list[PipelineStageEvent]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="PipelineStageEvent.created_at",
    )
    screening_questions: Mapped[list[ScreeningQuestion]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ScreeningQuestion.order_index",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"<Application id={self.id} candidate={self.candidate_id} "
            f"job={self.job_id} stage={self.stage}>"
        )


class PipelineStageEvent(Base, TimestampMixin):
    """One recorded stage transition (audit trail / activity feed)."""

    __tablename__ = "pipeline_stage_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False
    )
    from_stage: Mapped[str | None] = mapped_column(String(20))  # None for the initial event
    to_stage: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="stage_events")
