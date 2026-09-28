"""Candidate endpoints: upload resumes, list, detail, notes, tags, delete."""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from app.api.deps import DbSession, EmbeddingsDep, LLMDep, SettingsDep
from app.api.serializers import (
    candidate_list_item,
    candidate_out,
    note_out,
    tag_out,
)
from app.core.errors import ValidationAppError
from app.schemas.candidate import CandidateListItem, CandidateOut
from app.schemas.misc import NoteCreate, NoteOut, TagCreate, TagOut
from app.services import candidate_service

router = APIRouter(prefix="/candidates", tags=["candidates"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.get("", response_model=list[CandidateListItem], summary="List candidates")
def list_candidates(
    db: DbSession,
    q: str | None = None,
    skill: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[CandidateListItem]:
    candidates = candidate_service.list_candidates(db, q=q, skill=skill, limit=limit, offset=offset)
    return [candidate_list_item(candidate) for candidate in candidates]


@router.post(
    "/upload",
    response_model=CandidateOut,
    status_code=201,
    summary="Upload a resume (PDF/DOCX/TXT) and extract a structured profile",
)
def upload_resume(
    db: DbSession,
    llm: LLMDep,
    embeddings: EmbeddingsDep,
    settings: SettingsDep,
    file: UploadFile = File(..., description="Resume file"),
) -> CandidateOut:
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValidationAppError("File is too large — the limit is 10 MB.")
    candidate = candidate_service.ingest_resume(
        db,
        filename=file.filename or "resume.txt",
        data=data,
        provider=llm,
        embedding_provider=embeddings,
        upload_dir=settings.upload_dir,
    )
    return candidate_out(candidate)


@router.get("/{candidate_id}", response_model=CandidateOut, summary="Candidate detail")
def get_candidate(candidate_id: int, db: DbSession) -> CandidateOut:
    return candidate_out(candidate_service.get_candidate(db, candidate_id))


@router.delete("/{candidate_id}", status_code=204, summary="Delete a candidate")
def delete_candidate(candidate_id: int, db: DbSession) -> None:
    candidate_service.delete_candidate(db, candidate_id)


@router.post("/{candidate_id}/notes", response_model=NoteOut, status_code=201, summary="Add a note")
def add_note(candidate_id: int, payload: NoteCreate, db: DbSession) -> NoteOut:
    note = candidate_service.add_note(
        db,
        candidate_id,
        body=payload.body,
        author=payload.author,
        job_id=payload.job_id,
    )
    return note_out(note)


@router.delete("/{candidate_id}/notes/{note_id}", status_code=204, summary="Delete a note")
def delete_note(candidate_id: int, note_id: int, db: DbSession) -> None:
    candidate_service.get_candidate(db, candidate_id)  # 404 when the candidate is gone
    candidate_service.delete_note(db, note_id)


@router.post("/{candidate_id}/tags", response_model=TagOut, status_code=201, summary="Add a tag")
def add_tag(candidate_id: int, payload: TagCreate, db: DbSession) -> TagOut:
    tag = candidate_service.add_tag(db, candidate_id, name=payload.name, color=payload.color)
    return tag_out(tag)


@router.delete("/{candidate_id}/tags/{tag_id}", status_code=204, summary="Remove a tag")
def remove_tag(candidate_id: int, tag_id: int, db: DbSession) -> None:
    candidate_service.remove_tag(db, candidate_id, tag_id)
