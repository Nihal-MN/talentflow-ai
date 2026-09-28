"""Generated screening questions, persisted per application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.application import Application


class ScreeningQuestion(Base, TimestampMixin):
    """One candidate-specific screening question.

    ``category``: technical | experience | gap_probe | behavioral.
    ``source`` records the generating provider ("openai" | "mock").
    """

    __tablename__ = "screening_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(40), default="technical", nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30), default="mock", nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    application: Mapped[Application] = relationship(back_populates="screening_questions")
