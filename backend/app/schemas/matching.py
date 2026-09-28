"""Matching schemas — mirrors ``app.services.matching`` value objects."""

from __future__ import annotations

from pydantic import BaseModel


class EvidenceOut(BaseModel):
    snippet: str
    source: str
    match_type: str
    detail: str | None = None


class RequirementEvaluationOut(BaseModel):
    requirement_id: int
    kind: str
    category: str
    label: str
    status: str  # met | partial | missing | unknown | advisory
    reason: str
    skill: str | None = None
    similarity: float | None = None
    evidence: list[EvidenceOut] = []


class MatchResultOut(BaseModel):
    """One fully explained candidate↔job match result."""

    candidate_id: int
    candidate_name: str
    job_id: int
    job_title: str
    application_id: int | None
    stage: str | None
    composite_score: float | None
    components: dict[str, float | None]
    weights_used: dict[str, float]
    formula: str
    coverage: dict[str, dict[str, int]]
    semantic_similarity: float | None
    engine_version: str
    generated_at: str
    requirements: list[RequirementEvaluationOut]
