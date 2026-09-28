"""Embedding storage with a dialect-aware column type.

Vectors live in ``embedding_records``. On PostgreSQL the ``embedding`` column
is a native pgvector ``vector(1536)`` column (HNSW-indexed in the migration);
on SQLite (dev/tests) it degrades to JSON-encoded text and similarity is
computed in-process. All dialect handling is quarantined here and in
``app/services/embeddings_store.py`` — see docs/adr/0004.

Values are sent as text (``'[1.0,2.0,...]'``) and cast explicitly in SQL, so
the column works with or without the pgvector psycopg adapter registered.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import Index, Integer, String, Text, TypeDecorator, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import DEFAULT_EMBEDDING_DIM
from app.db.base import Base, TimestampMixin

#: Fixed vector dimension — shared by the OpenAI embedder and the mock embedder.
EMBEDDING_DIM = DEFAULT_EMBEDDING_DIM


class EmbeddingVector(TypeDecorator):
    """``vector(1536)`` on PostgreSQL; JSON-encoded TEXT elsewhere."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector

            return dialect.type_descriptor(Vector(EMBEDDING_DIM))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        encoded = json.dumps([float(x) for x in value])
        if dialect.name == "postgresql":
            # A plain text parameter is coerced by PostgreSQL into the vector
            # column type via its input function.
            return encoded
        return encoded

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            return [float(x) for x in json.loads(value)]
        return [float(x) for x in value]  # list or ndarray from a vector adapter


class EmbeddingRecord(Base, TimestampMixin):
    """One embedded text chunk belonging to a candidate, job or requirement."""

    __tablename__ = "embedding_records"
    __table_args__ = (
        Index("ix_embedding_records_owner", "owner_type", "owner_id"),
        UniqueConstraint("owner_type", "owner_id", "chunk_index"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # candidate | job | requirement
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    #: Which embedder produced this vector, e.g. "openai:text-embedding-3-small"
    #: or "mock:hashed-ngram-v1". Prevents silently mixing vector spaces.
    embedder: Mapped[str] = mapped_column(String(120), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<EmbeddingRecord {self.owner_type}:{self.owner_id}#{self.chunk_index}>"


def vector_to_literal(vector: list[float]) -> str:
    """Serialize a vector to pgvector's text form (``'[1,2,3]'``) for raw SQL."""
    return json.dumps([float(x) for x in vector])


def _coerce_value(value: Any) -> list[float] | None:  # pragma: no cover - helper
    if value is None:
        return None
    return [float(x) for x in value]
