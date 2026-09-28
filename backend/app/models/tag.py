"""Tags for lightweight candidate labelling."""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

#: Many-to-many association: candidates ↔ tags.
candidate_tags = Table(
    "candidate_tags",
    Base.metadata,
    Column("candidate_id", ForeignKey("candidates.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base, TimestampMixin):
    """A reusable label, e.g. "strong-communicator", "dubai-based"."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="slate", nullable=False)
