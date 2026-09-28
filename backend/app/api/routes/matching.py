"""Matching endpoints — ranked, fully explained candidate↔job evaluations."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DbSession, EmbeddingsDep
from app.api.serializers import match_result_out
from app.schemas.matching import MatchResultOut
from app.services import candidate_service, job_service
from app.services.matching import evaluate_pair, rank_candidates_for_job, rank_jobs_for_candidate

router = APIRouter(prefix="/matching", tags=["matching"])


@router.get(
    "/job/{job_id}",
    response_model=list[MatchResultOut],
    summary="Rank candidates for a job (explained)",
)
def rank_for_job(
    job_id: int,
    db: DbSession,
    embeddings: EmbeddingsDep,
    limit: int = Query(default=25, ge=1, le=100),
    only_applicants: bool = False,
) -> list[MatchResultOut]:
    job = job_service.get_job(db, job_id)
    results = rank_candidates_for_job(
        db,
        job,
        limit=limit,
        only_applicants=only_applicants,
        embedding_provider=embeddings,
    )
    return [match_result_out(result) for result in results]


@router.get(
    "/candidate/{candidate_id}",
    response_model=list[MatchResultOut],
    summary="Rank open jobs for a candidate (explained)",
)
def rank_for_candidate(
    candidate_id: int,
    db: DbSession,
    embeddings: EmbeddingsDep,
    limit: int = Query(default=10, ge=1, le=50),
) -> list[MatchResultOut]:
    candidate = candidate_service.get_candidate(db, candidate_id)
    results = rank_jobs_for_candidate(db, candidate, limit=limit, embedding_provider=embeddings)
    return [match_result_out(result) for result in results]


@router.get(
    "/pair",
    response_model=MatchResultOut,
    summary="Explain one candidate↔job pair",
)
def match_pair(
    db: DbSession,
    embeddings: EmbeddingsDep,
    job_id: int = Query(..., ge=1),
    candidate_id: int = Query(..., ge=1),
) -> MatchResultOut:
    job = job_service.get_job(db, job_id)
    candidate = candidate_service.get_candidate(db, candidate_id)
    result = evaluate_pair(db, candidate, job, embedding_provider=embeddings)
    return match_result_out(result)
