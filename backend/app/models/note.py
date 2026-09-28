"""Recruiter notes attached to candidates (optionally in a job context)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.candidate import Candidate


class CandidateNote(Base, TimestampMixin):
    """A free-text recruiter note."""

    __tablename__ = "candidate_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[int | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"), index=True
    )
    author: Mapped[str] = mapped_column(String(120), default="Recruiter", nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="notes")
