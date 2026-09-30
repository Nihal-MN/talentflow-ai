"""Candidate services: the resume ingestion pipeline, profile queries, notes,
tags and deletion. All candidate mutations flow through this module.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.ai.base import EmbeddingProvider, LLMProvider
from app.core.errors import NotFoundError, ValidationAppError
from app.models.candidate import (
    Candidate,
    CandidateCertification,
    CandidateEducation,
    CandidateExperience,
    CandidateSkill,
)
from app.models.note import CandidateNote
from app.models.tag import Tag, candidate_tags
from app.services import embeddings_store
from app.services.documents import extract_text, save_upload
from app.services.normalization import normalize_candidate

logger = logging.getLogger("talentflow.candidates")

_CANDIDATE_LOADERS = (
    selectinload(Candidate.experiences),
    selectinload(Candidate.educations),
    selectinload(Candidate.skills),
    selectinload(Candidate.certifications),
    selectinload(Candidate.tags),
    selectinload(Candidate.notes),
    selectinload(Candidate.applications),
)


def ingest_resume(
    db: Session,
    *,
    filename: str,
    data: bytes,
    provider: LLMProvider,
    embedding_provider: EmbeddingProvider,
    upload_dir: str,
) -> Candidate:
    """Resume → text extraction → structured extraction → validation → DB.

    The raw document is stored for audit/evidence; the structured profile is
    what the rest of the system reads.
    """
    text = extract_text(filename, data)
    stored_path = save_upload(filename, data, upload_dir)

    extracted = normalize_candidate(provider.extract_candidate(text, source_filename=filename))

    candidate = Candidate(
        full_name=extracted.full_name,
        email=extracted.email,
        phone=extracted.phone,
        location=extracted.location,
        headline=extracted.headline,
        summary=extracted.summary,
        years_experience=extracted.years_experience,
        linkedin_url=extracted.linkedin_url,
        github_url=extracted.github_url,
        website_url=extracted.website_url,
        resume_filename=filename,
        resume_path=stored_path,
        resume_text=text,
        extraction_method=provider.name,
        extraction_model=provider.model,
    )
    for index, experience in enumerate(extracted.experiences):
        candidate.experiences.append(
            CandidateExperience(
                company=experience.company,
                title=experience.title,
                location=experience.location,
                start_date=experience.start_date,
                end_date=experience.end_date,
                is_current=experience.is_current,
                description=experience.description,
                order_index=index,
            )
        )
    for index, education in enumerate(extracted.educations):
        candidate.educations.append(
            CandidateEducation(
                institution=education.institution,
                degree=education.degree,
                field_of_study=education.field_of_study,
                start_year=education.start_year,
                end_year=education.end_year,
                order_index=index,
            )
        )
    for skill in extracted.skills:
        candidate.skills.append(
            CandidateSkill(
                name=skill.name,
                normalized_name=skill.normalized_name,
                category=skill.category,
                evidence=skill.evidence,
            )
        )
    for certification in extracted.certifications:
        candidate.certifications.append(
            CandidateCertification(
                name=certification.name,
                issuer=certification.issuer,
                year=certification.year,
            )
        )

    db.add(candidate)
    db.flush()

    chunks = embeddings_store.build_candidate_chunks(candidate)
    embeddings_store.store_for_owner(
        db,
        owner_type="candidate",
        owner_id=candidate.id,
        chunks=chunks,
        provider=embedding_provider,
    )
    db.commit()
    db.refresh(candidate)

    logger.info(
        "candidate ingested",
        extra={
            "candidate_id": candidate.id,
            "skills": len(candidate.skills),
            "roles": len(candidate.experiences),
            "provider": provider.name,
        },
    )
    return candidate


def get_candidate(db: Session, candidate_id: int) -> Candidate:
    """Fetch a candidate with everything needed by the detail page."""
    candidate = db.execute(
        select(Candidate).where(Candidate.id == candidate_id).options(*_CANDIDATE_LOADERS)
    ).scalar_one_or_none()
    if candidate is None:
        raise NotFoundError(f"Candidate {candidate_id} does not exist.")
    return candidate


def list_candidates(
    db: Session,
    *,
    q: str | None = None,
    skill: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Candidate]:
    """List candidates (optionally filtered), newest first."""
    statement = (
        select(Candidate)
        .options(*_CANDIDATE_LOADERS)
        .order_by(Candidate.created_at.desc(), Candidate.id.desc())
        .limit(max(1, min(limit, 200)))
        .offset(max(0, offset))
    )
    if q:
        pattern = f"%{q.strip()}%"
        statement = statement.where(
            Candidate.full_name.ilike(pattern)
            | Candidate.headline.ilike(pattern)
            | Candidate.location.ilike(pattern)
        )
    if skill:
        statement = statement.where(
            Candidate.skills.any(CandidateSkill.normalized_name == skill.strip().lower())
        )
    return list(db.execute(statement).scalars())


def count_candidates(
    db: Session,
    *,
    q: str | None = None,
    skill: str | None = None,
) -> int:
    """Total candidates matching the same filters as :func:`list_candidates`."""
    statement = select(func.count()).select_from(Candidate)
    if q:
        pattern = f"%{q.strip()}%"
        statement = statement.where(
            Candidate.full_name.ilike(pattern)
            | Candidate.headline.ilike(pattern)
            | Candidate.location.ilike(pattern)
        )
    if skill:
        statement = statement.where(
            Candidate.skills.any(CandidateSkill.normalized_name == skill.strip().lower())
        )
    return int(db.execute(statement).scalar_one())


def delete_candidate(db: Session, candidate_id: int) -> None:
    """Delete a candidate, their rows (cascade) and their embeddings."""
    candidate = get_candidate(db, candidate_id)
    embeddings_store.delete_for_owner(db, "candidate", candidate.id)
    db.delete(candidate)
    db.commit()
    logger.info("candidate deleted", extra={"candidate_id": candidate_id})


# ── Notes ───────────────────────────────────────────────────────────────────


def add_note(
    db: Session,
    candidate_id: int,
    *,
    body: str,
    author: str = "Recruiter",
    job_id: int | None = None,
) -> CandidateNote:
    """Add a recruiter note to a candidate."""
    text = (body or "").strip()
    if not text:
        raise ValidationAppError("Note text cannot be empty.")
    get_candidate(db, candidate_id)  # 404 if missing
    note = CandidateNote(
        candidate_id=candidate_id,
        job_id=job_id,
        author=author.strip() or "Recruiter",
        body=text[:4000],
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note_id: int) -> None:
    """Delete a note by id."""
    note = db.get(CandidateNote, note_id)
    if note is None:
        raise NotFoundError(f"Note {note_id} does not exist.")
    db.delete(note)
    db.commit()


# ── Tags ────────────────────────────────────────────────────────────────────


def add_tag(db: Session, candidate_id: int, *, name: str, color: str = "slate") -> Tag:
    """Attach a tag to a candidate (creating the tag when new)."""
    clean = (name or "").strip().lower()[:60]
    if not clean:
        raise ValidationAppError("Tag name cannot be empty.")
    candidate = get_candidate(db, candidate_id)
    tag = db.execute(select(Tag).where(func.lower(Tag.name) == clean)).scalar_one_or_none()
    if tag is None:
        tag = Tag(name=clean, color=color if color in TAG_COLORS else "slate")
        db.add(tag)
        db.flush()
    if tag not in candidate.tags:
        candidate.tags.append(tag)
    db.commit()
    db.refresh(tag)
    return tag


def remove_tag(db: Session, candidate_id: int, tag_id: int) -> None:
    """Detach a tag from a candidate."""
    candidate = get_candidate(db, candidate_id)
    tag = db.get(Tag, tag_id)
    if tag is None or tag not in candidate.tags:
        raise NotFoundError(f"Tag {tag_id} is not attached to candidate {candidate_id}.")
    candidate.tags.remove(tag)
    db.commit()


TAG_COLORS = {"slate", "emerald", "amber", "rose", "violet", "sky", "teal"}


def list_tags(db: Session) -> list[tuple[Tag, int]]:
    """All tags with their candidate usage counts, most used first."""
    rows = db.execute(
        select(Tag, func.count(candidate_tags.c.candidate_id))
        .outerjoin(candidate_tags, candidate_tags.c.tag_id == Tag.id)
        .group_by(Tag.id)
        .order_by(func.count(candidate_tags.c.candidate_id).desc(), Tag.name)
    ).all()
    return [(tag, count) for tag, count in rows]
