"""Job services: create jobs from pasted text or uploaded files, persist
extracted requirements, and provide queries for the API layer.

All database mutations for jobs flow through this module (see ADR 0001);
routers never touch models directly.
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.ai.base import EmbeddingProvider, LLMProvider
from app.core.errors import NotFoundError, ValidationAppError
from app.models.job import Job, JobRequirement
from app.services import embeddings_store
from app.services.documents import extract_text, save_upload
from app.services.normalization import normalize_job

logger = logging.getLogger("talentflow.jobs")

MIN_DESCRIPTION_CHARS = 30


def create_job(
    db: Session,
    *,
    title: str,
    jd_text: str,
    company: str = "",
    location: str | None = None,
    employment_type: str | None = None,
    provider: LLMProvider,
    embedding_provider: EmbeddingProvider,
    source: str = "manual",
) -> Job:
    """Create a job by extracting structured requirements from its JD."""
    text = (jd_text or "").strip()
    if len(text) < MIN_DESCRIPTION_CHARS:
        raise ValidationAppError(
            f"Job description is too short ({len(text)} chars). "
            f"Paste at least {MIN_DESCRIPTION_CHARS} characters, or upload a file instead."
        )

    extracted = normalize_job(provider.extract_job(text))

    job = Job(
        title=(title or "").strip() or extracted.title,
        company=(company or "").strip() or (extracted.company or ""),
        location=(location or "").strip() or extracted.location,
        employment_type=(employment_type or "").strip() or extracted.employment_type or "full_time",
        seniority=extracted.seniority,
        domain=extracted.domain,
        description_text=text,
        source=source,
        extraction_method=provider.name,
        extraction_model=provider.model,
    )
    for index, requirement in enumerate(extracted.requirements):
        job.requirements.append(
            JobRequirement(
                kind=requirement.kind,
                category=requirement.category,
                label=requirement.label,
                normalized_skill=requirement.normalized_skill,
                min_years=requirement.min_years,
                keywords=",".join(requirement.keywords) or None,
                order_index=index,
            )
        )
    db.add(job)
    db.flush()

    chunks = embeddings_store.build_job_chunks(job)
    embeddings_store.store_for_owner(
        db, owner_type="job", owner_id=job.id, chunks=chunks, provider=embedding_provider
    )
    db.commit()
    db.refresh(job)

    logger.info(
        "job created",
        extra={
            "job_id": job.id,
            "requirements": len(job.requirements),
            "provider": provider.name,
            "mode": source,
        },
    )
    return job


def create_job_from_upload(
    db: Session,
    *,
    filename: str,
    data: bytes,
    title: str = "",
    company: str = "",
    provider: LLMProvider,
    embedding_provider: EmbeddingProvider,
    upload_dir: str,
) -> Job:
    """Create a job from an uploaded JD document (PDF/DOCX/TXT)."""
    text = extract_text(filename, data)
    save_upload(filename, data, upload_dir)
    return create_job(
        db,
        title=title or _title_from_filename(filename),
        jd_text=text,
        company=company,
        provider=provider,
        embedding_provider=embedding_provider,
        source="upload",
    )


def get_job(db: Session, job_id: int) -> Job:
    """Fetch a job with requirements + applications (or raise NotFoundError)."""
    job = db.execute(
        select(Job)
        .where(Job.id == job_id)
        .options(selectinload(Job.requirements), selectinload(Job.applications))
    ).scalar_one_or_none()
    if job is None:
        raise NotFoundError(f"Job {job_id} does not exist.")
    return job


def list_jobs(
    db: Session,
    *,
    status: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Job]:
    """List jobs (optionally filtered), newest first."""
    statement = (
        select(Job)
        .options(selectinload(Job.requirements), selectinload(Job.applications))
        .order_by(Job.created_at.desc(), Job.id.desc())
        .limit(max(1, min(limit, 200)))
        .offset(max(0, offset))
    )
    if status:
        statement = statement.where(Job.status == status)
    if q:
        pattern = f"%{q.strip()}%"
        statement = statement.where(Job.title.ilike(pattern) | Job.company.ilike(pattern))
    return list(db.execute(statement).scalars())


def count_jobs(
    db: Session,
    *,
    status: str | None = None,
    q: str | None = None,
) -> int:
    """Total jobs matching the same filters as :func:`list_jobs`."""
    statement = select(func.count()).select_from(Job)
    if status:
        statement = statement.where(Job.status == status)
    if q:
        pattern = f"%{q.strip()}%"
        statement = statement.where(Job.title.ilike(pattern) | Job.company.ilike(pattern))
    return int(db.execute(statement).scalar_one())


def update_job(
    db: Session,
    job_id: int,
    *,
    status: str | None = None,
    title: str | None = None,
    company: str | None = None,
    location: str | None = None,
) -> Job:
    """Update mutable job fields (status/title/company/location)."""
    job = get_job(db, job_id)
    if status is not None:
        if status not in {"open", "paused", "closed"}:
            raise ValidationAppError("Job status must be one of: open, paused, closed.")
        job.status = status
    if title is not None and title.strip():
        job.title = title.strip()
    if company is not None:
        job.company = company.strip()
    if location is not None:
        job.location = location.strip() or None
    db.commit()
    db.refresh(job)
    return job


def delete_job(db: Session, job_id: int) -> None:
    """Delete a job, its applications (cascade) and its embeddings."""
    job = get_job(db, job_id)
    embeddings_store.delete_for_owner(db, "job", job.id)
    db.delete(job)
    db.commit()
    logger.info("job deleted", extra={"job_id": job_id})


def _title_from_filename(filename: str) -> str:
    stem = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    cleaned = stem.replace("_", " ").replace("-", " ").strip()
    return cleaned.title() if cleaned else "Job"
