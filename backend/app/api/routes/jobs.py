"""Job endpoints: create (paste/upload), list, detail, update, delete."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, Response, UploadFile

from app.api.deps import DbSession, EmbeddingsDep, LLMDep, SettingsDep
from app.api.serializers import job_list_item, job_out
from app.core.errors import ValidationAppError
from app.schemas.job import JobCreate, JobListItem, JobOut, JobUpdate
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.get("", response_model=list[JobListItem], summary="List jobs")
def list_jobs(
    db: DbSession,
    response: Response,
    status: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[JobListItem]:
    jobs = job_service.list_jobs(db, status=status, q=q, limit=limit, offset=offset)
    response.headers["X-Total-Count"] = str(job_service.count_jobs(db, status=status, q=q))
    return [job_list_item(job) for job in jobs]


@router.post("", response_model=JobOut, status_code=201, summary="Create a job from pasted text")
def create_job(
    payload: JobCreate,
    db: DbSession,
    llm: LLMDep,
    embeddings: EmbeddingsDep,
) -> JobOut:
    job = job_service.create_job(
        db,
        title=payload.title or "",
        jd_text=payload.jd_text,
        company=payload.company,
        location=payload.location,
        employment_type=payload.employment_type,
        provider=llm,
        embedding_provider=embeddings,
    )
    return job_out(job)


@router.post("/upload", response_model=JobOut, status_code=201, summary="Create a job from a file")
def create_job_from_file(
    db: DbSession,
    llm: LLMDep,
    embeddings: EmbeddingsDep,
    settings: SettingsDep,
    file: UploadFile = File(..., description="PDF, DOCX or TXT job description"),
    title: str = Form(""),
    company: str = Form(""),
) -> JobOut:
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValidationAppError("File is too large — the limit is 10 MB.")
    job = job_service.create_job_from_upload(
        db,
        filename=file.filename or "job.txt",
        data=data,
        title=title,
        company=company,
        provider=llm,
        embedding_provider=embeddings,
        upload_dir=settings.upload_dir,
    )
    return job_out(job)


@router.get("/{job_id}", response_model=JobOut, summary="Job detail (with requirements)")
def get_job(job_id: int, db: DbSession) -> JobOut:
    return job_out(job_service.get_job(db, job_id))


@router.patch("/{job_id}", response_model=JobOut, summary="Update job fields")
def update_job(job_id: int, payload: JobUpdate, db: DbSession) -> JobOut:
    job = job_service.update_job(
        db,
        job_id,
        status=payload.status,
        title=payload.title,
        company=payload.company,
        location=payload.location,
    )
    return job_out(job)


@router.delete("/{job_id}", status_code=204, summary="Delete a job")
def delete_job(job_id: int, db: DbSession) -> None:
    job_service.delete_job(db, job_id)
