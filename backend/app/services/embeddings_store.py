"""Embedding storage and similarity search — the ONE dialect-aware module.

* PostgreSQL: pgvector ``<=>`` cosine distance in SQL (HNSW-indexed column).
* SQLite (dev/tests): in-process cosine over the owner's rows.

Chunk text is stored alongside every vector so any semantic hit can be traced
back to real source text. See docs/adr/0004.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import Float, bindparam, cast, delete, select, type_coerce
from sqlalchemy.orm import Session

from app.ai.base import EmbeddingProvider
from app.ai.embeddings import cosine_similarity
from app.core.errors import ValidationAppError
from app.models.embedding import EMBEDDING_DIM, EmbeddingRecord, vector_to_literal

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.job import Job

logger = logging.getLogger(__name__)

MAX_CHUNKS_PER_OWNER = 24
MAX_CHUNK_CHARS = 1500


@dataclass(slots=True)
class SimilarChunk:
    """A ranked semantic-search hit."""

    owner_type: str
    owner_id: int
    chunk_index: int
    chunk_text: str
    similarity: float


def delete_for_owner(db: Session, owner_type: str, owner_id: int) -> None:
    """Remove all vectors for an owner (idempotent re-embedding).

    Uses a bulk DELETE (executed immediately) rather than ORM unit-of-work
    deletion, so a following INSERT in the same flush cannot hit the
    (owner_type, owner_id, chunk_index) unique constraint.
    """
    db.execute(
        delete(EmbeddingRecord).where(
            EmbeddingRecord.owner_type == owner_type,
            EmbeddingRecord.owner_id == owner_id,
        )
    )


def store_for_owner(
    db: Session,
    *,
    owner_type: str,
    owner_id: int,
    chunks: list[str],
    provider: EmbeddingProvider,
) -> int:
    """Embed and store chunks for an owner; returns the number stored."""
    cleaned: list[str] = []
    for chunk in chunks:
        text = (chunk or "").strip()[:MAX_CHUNK_CHARS]
        if text:
            cleaned.append(text)
    cleaned = cleaned[:MAX_CHUNKS_PER_OWNER]

    delete_for_owner(db, owner_type, owner_id)
    if not cleaned:
        return 0

    vectors = provider.embed(cleaned)
    for vector in vectors:
        if len(vector) != EMBEDDING_DIM:
            raise ValidationAppError(
                f"Embedding dimension mismatch: provider returned {len(vector)}, "
                f"storage expects {EMBEDDING_DIM}. Check OPENAI_EMBEDDING_MODEL/embedding_dim."
            )
    embedder_name = f"{provider.name}:{provider.model}"
    for index, (chunk, vector) in enumerate(zip(cleaned, vectors, strict=False)):
        db.add(
            EmbeddingRecord(
                owner_type=owner_type,
                owner_id=owner_id,
                chunk_index=index,
                chunk_text=chunk,
                embedder=embedder_name,
                embedding=vector,
            )
        )
    db.flush()
    return len(cleaned)


def get_owner_chunks(db: Session, owner_type: str, owner_id: int) -> list[EmbeddingRecord]:
    """All stored chunks for one owner, ordered by chunk index."""
    return list(
        db.execute(
            select(EmbeddingRecord)
            .where(
                EmbeddingRecord.owner_type == owner_type,
                EmbeddingRecord.owner_id == owner_id,
                EmbeddingRecord.embedding.is_not(None),
            )
            .order_by(EmbeddingRecord.chunk_index)
        ).scalars()
    )


def search_similar(
    db: Session,
    *,
    owner_type: str,
    query_vector: list[float],
    limit: int = 10,
    exclude_owner_id: int | None = None,
) -> list[SimilarChunk]:
    """Rank stored chunks of ``owner_type`` by cosine similarity to the query."""
    dialect = db.get_bind().dialect.name
    conditions = [
        EmbeddingRecord.owner_type == owner_type,
        EmbeddingRecord.embedding.is_not(None),
    ]
    if exclude_owner_id is not None:
        conditions.append(EmbeddingRecord.owner_id != exclude_owner_id)

    if dialect == "postgresql":
        from pgvector.sqlalchemy import Vector

        vector_param = bindparam("query_vector", value=vector_to_literal(query_vector))
        # The <=> operator expression would otherwise inherit the *vector*
        # column's result type; type_coerce tells SQLAlchemy this yields a
        # plain float distance (SQL unchanged, result processing correct).
        distance = type_coerce(
            EmbeddingRecord.embedding.op("<=>")(cast(vector_param, Vector(EMBEDDING_DIM))),
            Float,
        )
        rows = db.execute(
            select(EmbeddingRecord, distance.label("distance"))
            .where(*conditions)
            .order_by(distance)
            .limit(max(1, limit))
        ).all()
        return [
            SimilarChunk(
                owner_type=record.owner_type,
                owner_id=record.owner_id,
                chunk_index=record.chunk_index,
                chunk_text=record.chunk_text,
                similarity=round(1.0 - float(distance), 6),
            )
            for record, distance in rows
        ]

    # SQLite / anything else: in-process cosine over the (demo-scale) table.
    scored: list[SimilarChunk] = []
    for record in db.execute(select(EmbeddingRecord).where(*conditions)).scalars():
        similarity = cosine_similarity(query_vector, record.embedding or [])
        scored.append(
            SimilarChunk(
                owner_type=record.owner_type,
                owner_id=record.owner_id,
                chunk_index=record.chunk_index,
                chunk_text=record.chunk_text,
                similarity=round(similarity, 6),
            )
        )
    scored.sort(key=lambda hit: hit.similarity, reverse=True)
    return scored[: max(1, limit)]


def search_similar_text(
    db: Session,
    *,
    owner_type: str,
    text: str,
    provider: EmbeddingProvider,
    limit: int = 10,
    exclude_owner_id: int | None = None,
) -> list[SimilarChunk]:
    """Convenience: embed ``text`` with ``provider`` and search."""
    if not text.strip():
        return []
    (vector,) = provider.embed([text])
    return search_similar(
        db,
        owner_type=owner_type,
        query_vector=vector,
        limit=limit,
        exclude_owner_id=exclude_owner_id,
    )


# ── Chunk builders (structured fields, never hidden text) ───────────────────


def build_candidate_chunks(candidate: Candidate) -> list[str]:
    """Candidate chunks: summary, each role, skills, education — traceable."""
    chunks: list[str] = []
    header_bits = [candidate.full_name]
    if candidate.headline:
        header_bits.append(candidate.headline)
    if candidate.location:
        header_bits.append(candidate.location)
    if candidate.years_experience is not None:
        header_bits.append(f"{candidate.years_experience:g} years of experience")
    chunks.append(". ".join(header_bits))

    if candidate.summary:
        chunks.append(f"Summary: {candidate.summary}")
    for experience in candidate.experiences:
        parts = [part for part in [experience.title, experience.company] if part]
        line = " at ".join(parts) if len(parts) == 2 else (parts[0] if parts else "Role")
        if experience.start_date:
            period = f"{experience.start_date:%Y-%m}"
            period += (
                "–present"
                if experience.is_current or not experience.end_date
                else f"–{experience.end_date:%Y-%m}"
            )
            line += f" ({period})"
        if experience.description:
            line += f": {experience.description}"
        chunks.append(line)
    if candidate.skills:
        chunks.append("Skills: " + ", ".join(skill.normalized_name for skill in candidate.skills))
    for education in candidate.educations:
        line = " — ".join(part for part in [education.degree, education.institution] if part)
        if line:
            chunks.append(f"Education: {line}")
    return chunks


def build_job_chunks(job: Job) -> list[str]:
    """Job chunks: an overview chunk plus one chunk per requirement."""
    overview = f"{job.title}"
    if job.company:
        overview += f" at {job.company}"
    details = [
        bit
        for bit in [
            job.location,
            job.seniority and f"{job.seniority} level",
            job.domain and f"{job.domain} domain",
        ]
        if bit
    ]
    if details:
        overview += " — " + ", ".join(details)
    if job.description_text:
        overview += f". {job.description_text[:600]}"
    chunks = [overview]
    for requirement in job.requirements:
        prefix = "Required" if requirement.kind == "must_have" else "Preferred"
        text = f"{prefix}: {requirement.label}"
        if (
            requirement.normalized_skill
            and requirement.normalized_skill not in requirement.label.lower()
        ):
            text += f" ({requirement.normalized_skill})"
        chunks.append(text)
    return chunks
