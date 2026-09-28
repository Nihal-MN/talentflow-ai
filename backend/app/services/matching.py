"""Explainable candidate↔job matching — deterministic first, no opaque score.

Layers (see docs/adr/0003):

1. deterministic requirement evaluation → met / partial / missing / unknown,
2. normalized skill matching with alias & family relatedness,
3. semantic similarity as a supporting signal (never overriding a hard miss),
4. evidence extraction — quoted, traceable snippets,
5. a transparent composite with published weights.

Hard rules: no protected characteristics are used or inferred; no hire/no-hire
verdict is produced — the recruiter decides. Every number shown can be
re-derived from the inputs shown.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.base import EmbeddingProvider
from app.ai.embeddings import cosine_similarity
from app.models.application import Application
from app.models.candidate import Candidate
from app.services.embeddings_store import get_owner_chunks
from app.services.matching_evidence import candidate_haystack, first_mention, terms_from_requirement
from app.services.skills import are_related, canonicalize

if TYPE_CHECKING:
    from app.models.job import Job, JobRequirement

logger = logging.getLogger(__name__)

#: Published composite weights (re-normalized over the components that exist).
WEIGHTS = {"must_have": 0.60, "preferred": 0.20, "experience": 0.10, "domain": 0.10}
#: Weight given to missed requirements in coverage math.
STATUS_SCORES = {"met": 1.0, "partial": 0.5, "missing": 0.0}
#: A candidate within this many years of the requirement gets partial credit.
PARTIAL_YEARS_TOLERANCE = 1.5
#: Minimum semantic similarity for a soft-requirement chunk to count as evidence.
SOFT_EVIDENCE_SIMILARITY = 0.35

ENGINE_VERSION = "matching-engine-v1"

_COMPOSITE_EXCLUDED_CATEGORIES = {"experience", "domain"}  # scored as their own components

#: Degree-equivalence groups: any variant found in the requirement label
#: expands the match terms to the full group ("Bachelor's" ↔ "BSc").
_DEGREE_SYNONYMS = {
    "bachelor": [
        "bachelor",
        "bachelors",
        "bsc",
        "b.sc",
        "ba",
        "b.a",
        "beng",
        "b.eng",
        "btech",
        "b.tech",
        "undergraduate",
    ],
    "master": [
        "master",
        "masters",
        "msc",
        "m.sc",
        "ma",
        "m.a",
        "mba",
        "meng",
        "m.eng",
        "mtech",
        "m.tech",
        "postgraduate",
    ],
    "phd": ["phd", "ph.d", "doctorate", "doctoral"],
    "diploma": ["diploma", "higher national"],
}


def _expand_degree_terms(label: str, terms: list[str]) -> list[str]:
    label_lower = label.lower()
    expanded = list(terms)
    for variants in _DEGREE_SYNONYMS.values():
        if any(re.search(rf"(?<![a-z]){re.escape(v)}(?![a-z])", label_lower) for v in variants):
            for variant in variants:
                if variant not in expanded:
                    expanded.append(variant)
    return expanded


@dataclass(slots=True)
class Evidence:
    """A traceable snippet supporting or contradicting an evaluation."""

    snippet: str
    source: str  # "resume_text" | "skills" | "experience" | "education" | "profile" | "job"
    match_type: str  # "lexical" | "computed" | "semantic"
    detail: str | None = None


@dataclass(slots=True)
class RequirementEvaluation:
    """The engine's verdict on ONE requirement, with its reasons."""

    requirement_id: int
    kind: str  # must_have | preferred
    category: str
    label: str
    status: str  # met | partial | missing | unknown | advisory
    reason: str
    skill: str | None = None  # canonical skill when the requirement is a skill
    evidence: list[Evidence] = field(default_factory=list)
    similarity: float | None = None


@dataclass(slots=True)
class MatchResult:
    """Full, self-describing match result for one candidate↔job pair."""

    candidate_id: int
    candidate_name: str
    job_id: int
    job_title: str
    application_id: int | None
    stage: str | None
    composite_score: float | None  # 0-100, None when nothing is evaluable
    components: dict[str, float | None]
    weights_used: dict[str, float]
    formula: str
    coverage: dict[str, dict[str, int]]
    semantic_similarity: float | None
    requirements: list[RequirementEvaluation]
    engine_version: str = ENGINE_VERSION
    generated_at: str = ""

    def as_dict(self) -> dict:
        """Plain-dict form for API serialization/tests."""
        return {
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "job_id": self.job_id,
            "job_title": self.job_title,
            "application_id": self.application_id,
            "stage": self.stage,
            "composite_score": self.composite_score,
            "components": self.components,
            "weights_used": self.weights_used,
            "formula": self.formula,
            "coverage": self.coverage,
            "semantic_similarity": self.semantic_similarity,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "requirements": [
                {
                    "requirement_id": item.requirement_id,
                    "kind": item.kind,
                    "category": item.category,
                    "label": item.label,
                    "status": item.status,
                    "reason": item.reason,
                    "skill": item.skill,
                    "similarity": item.similarity,
                    "evidence": [
                        {
                            "snippet": ev.snippet,
                            "source": ev.source,
                            "match_type": ev.match_type,
                            "detail": ev.detail,
                        }
                        for ev in item.evidence
                    ],
                }
                for item in self.requirements
            ],
        }


# ── Public API ──────────────────────────────────────────────────────────────


def evaluate_pair(
    db: Session,
    candidate: Candidate,
    job: Job,
    *,
    embedding_provider: EmbeddingProvider | None = None,
) -> MatchResult:
    """Evaluate one candidate against one job, fully explainably."""
    haystack = candidate_haystack(candidate)
    candidate_chunks = get_owner_chunks(db, owner_type="candidate", owner_id=candidate.id)

    evaluations = [
        _evaluate_requirement(
            db, candidate, requirement, haystack, candidate_chunks, embedding_provider
        )
        for requirement in job.requirements
    ]

    components, weights_used = _components(evaluations)
    composite, formula = _composite(components, weights_used)
    coverage = _coverage(evaluations)

    application = db.execute(
        select(Application).where(
            Application.candidate_id == candidate.id, Application.job_id == job.id
        )
    ).scalar_one_or_none()

    return MatchResult(
        candidate_id=candidate.id,
        candidate_name=candidate.full_name,
        job_id=job.id,
        job_title=job.title,
        application_id=application.id if application else None,
        stage=application.stage if application else None,
        composite_score=composite,
        components=components,
        weights_used=weights_used,
        formula=formula,
        coverage=coverage,
        semantic_similarity=_overall_similarity(db, candidate.id, job.id),
        requirements=evaluations,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


def rank_candidates_for_job(
    db: Session,
    job: Job,
    *,
    limit: int = 25,
    only_applicants: bool = False,
    embedding_provider: EmbeddingProvider | None = None,
) -> list[MatchResult]:
    """Rank all (or only applied) candidates for a job, best first."""
    statement = select(Candidate)
    if only_applicants:
        statement = statement.join(Application, Application.candidate_id == Candidate.id).where(
            Application.job_id == job.id
        )
    candidates = db.execute(statement).scalars().all()

    results = [
        evaluate_pair(db, candidate, job, embedding_provider=embedding_provider)
        for candidate in candidates
    ]
    results.sort(key=_ranking_key)
    return results[:limit]


def rank_jobs_for_candidate(
    db: Session,
    candidate: Candidate,
    *,
    limit: int = 10,
    embedding_provider: EmbeddingProvider | None = None,
) -> list[MatchResult]:
    """Rank open jobs for a candidate, best first."""
    from app.models.job import Job as JobModel

    jobs = db.execute(select(JobModel).where(JobModel.status == "open")).scalars().all()
    results = [
        evaluate_pair(db, candidate, job, embedding_provider=embedding_provider) for job in jobs
    ]
    results.sort(key=_ranking_key)
    return results[:limit]


def _ranking_key(result: MatchResult) -> tuple:
    met_must = result.coverage.get("must_have", {}).get("met", 0)
    return (
        -(result.composite_score if result.composite_score is not None else -1.0),
        -met_must,
        result.candidate_name.lower(),
        result.job_title.lower(),
    )


# ── Requirement evaluation ──────────────────────────────────────────────────


def _evaluate_requirement(
    db: Session,
    candidate: Candidate,
    requirement: JobRequirement,
    haystack: list[str],
    candidate_chunks: list,
    embedding_provider: EmbeddingProvider | None,
) -> RequirementEvaluation:
    category = requirement.category
    if category == "skill":
        status, reason, evidence = _evaluate_skill(candidate, requirement, haystack)
    elif category == "experience":
        status, reason, evidence = _evaluate_experience(candidate, requirement, haystack)
    elif category == "education":
        status, reason, evidence = _evaluate_education(candidate, requirement)
    elif category == "location":
        status, reason, evidence = _evaluate_location(candidate, requirement, haystack)
    elif category == "domain":
        status, reason, evidence = _evaluate_domain(candidate, requirement, haystack)
    elif category == "certification":
        status, reason, evidence = _evaluate_certification(candidate, requirement)
    else:
        status, reason, evidence = _evaluate_soft(
            requirement, haystack, candidate_chunks, embedding_provider
        )

    similarity = None
    if status == "advisory" and embedding_provider is not None and candidate_chunks:
        similarity = _label_similarity(requirement.label, candidate_chunks, embedding_provider)

    return RequirementEvaluation(
        requirement_id=requirement.id,
        kind=requirement.kind,
        category=category,
        label=requirement.label,
        status=status,
        reason=reason,
        skill=requirement.normalized_skill,
        evidence=evidence,
        similarity=similarity,
    )


def _evaluate_skill(
    candidate: Candidate, requirement: JobRequirement, haystack: list[str]
) -> tuple[str, str, list[Evidence]]:
    target = requirement.normalized_skill or canonicalize(requirement.label)
    terms = [
        term for term in ([target] if target else []) + terms_from_requirement(requirement) if term
    ]

    skill_map = {skill.normalized_name: skill for skill in candidate.skills}
    if target and target in skill_map:
        skill = skill_map[target]
        evidence = []
        if skill.evidence:
            evidence.append(
                Evidence(
                    snippet=skill.evidence,
                    source="skills",
                    match_type="lexical",
                    detail=f"skill '{target}' extracted from the resume",
                )
            )
        else:
            hit = first_mention(haystack, [target])
            if hit:
                evidence.append(
                    Evidence(
                        snippet=hit[1],
                        source="resume_text",
                        match_type="lexical",
                        detail=f"mention of '{hit[0]}'",
                    )
                )
        return "met", f"Skill '{target}' is present in the candidate's profile.", evidence

    if target:
        related = [
            skill for skill in candidate.skills if are_related(target, skill.normalized_name)
        ]
        if related:
            evidence = [
                Evidence(
                    snippet=skill.evidence or f"Skill: {skill.name}",
                    source="skills",
                    match_type="lexical",
                    detail=f"related skill '{skill.normalized_name}'",
                )
                for skill in related[:2]
            ]
            names = ", ".join(skill.normalized_name for skill in related[:3])
            return (
                "partial",
                f"No '{target}', but related skill(s) in the same family: {names}. "
                "Related skills earn partial credit only.",
                evidence,
            )

    hit = first_mention(haystack, terms)
    if hit and target:
        return (
            "met",
            f"'{target}' is not an extracted skill but appears in the resume text.",
            [
                Evidence(
                    snippet=hit[1],
                    source="resume_text",
                    match_type="lexical",
                    detail=f"mention of '{hit[0]}'",
                )
            ],
        )
    return (
        "missing",
        f"No evidence of '{target or requirement.label[:60]}' in the candidate's "
        "profile or resume.",
        [],
    )


def _evaluate_experience(
    candidate: Candidate, requirement: JobRequirement, haystack: list[str]
) -> tuple[str, str, list[Evidence]]:
    min_years = requirement.min_years
    years = candidate.years_experience

    if min_years is None:
        hit = first_mention(haystack, terms_from_requirement(requirement))
        evidence = (
            [
                Evidence(
                    snippet=hit[1],
                    source="resume_text",
                    match_type="lexical",
                    detail=f"mention of '{hit[0]}'",
                )
            ]
            if hit
            else []
        )
        return (
            "unknown",
            "Requirement states no explicit duration — not automatically scored.",
            evidence,
        )

    if years is None:
        return (
            "unknown",
            "Candidate's years of experience could not be resolved from dated roles.",
            [],
        )

    dated_roles = [exp for exp in candidate.experiences if exp.start_date]
    computed = Evidence(
        snippet=(
            f"Total ~{years:g} years across {len(dated_roles)} dated role(s), "
            "computed from resume dates."
        ),
        source="profile",
        match_type="computed",
        detail="years = merged date ranges of roles",
    )
    if years >= min_years:
        return "met", f"{years:g} years of experience ≥ required {min_years:g} years.", [computed]
    if years >= min_years - PARTIAL_YEARS_TOLERANCE:
        return (
            "partial",
            f"{years:g} years vs required {min_years:g} — within "
            f"{PARTIAL_YEARS_TOLERANCE:g} years, treat as close.",
            [computed],
        )
    return "missing", f"{years:g} years of experience vs required {min_years:g} years.", [computed]


def _evaluate_education(
    candidate: Candidate, requirement: JobRequirement
) -> tuple[str, str, list[Evidence]]:
    if not candidate.educations:
        return "unknown", "No education information on the candidate's profile.", []
    pool = " ".join(
        " ".join(part for part in [edu.degree, edu.institution, edu.field_of_study] if part)
        for edu in candidate.educations
    ).lower()
    terms = _expand_degree_terms(requirement.label, terms_from_requirement(requirement))
    matches = [term for term in terms if _word_in(term, pool)]
    evidence = [
        Evidence(
            snippet=" — ".join(part for part in [edu.degree, edu.institution] if part),
            source="education",
            match_type="lexical",
            detail=f"education entry matching '{matches[0]}'" if matches else None,
        )
        for edu in candidate.educations[:1]
    ]
    if matches:
        return (
            "met",
            f"Education matches requirement keyword(s): {', '.join(matches[:3])}.",
            evidence,
        )
    return "missing", "No education entry matches the requirement's keyword(s).", []


def _word_in(term: str, text: str) -> bool:
    """Word-boundary substring check (avoids 'ba' matching inside 'Barcelona')."""
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text))


def _evaluate_location(
    candidate: Candidate, requirement: JobRequirement, haystack: list[str]
) -> tuple[str, str, list[Evidence]]:
    label_lower = requirement.label.lower()
    if "remote" in label_lower:
        return (
            "met",
            "The requirement is remote-friendly.",
            [
                Evidence(
                    snippet=requirement.label,
                    source="job",
                    match_type="computed",
                    detail="remote role",
                )
            ],
        )
    terms = terms_from_requirement(requirement)
    if candidate.location:
        location_lower = candidate.location.lower()
        for term in terms:
            if term in location_lower or location_lower in term:
                return (
                    "met",
                    f"Candidate location '{candidate.location}' matches.",
                    [
                        Evidence(
                            snippet=candidate.location,
                            source="profile",
                            match_type="lexical",
                            detail=f"location field matches '{term}'",
                        )
                    ],
                )
    hit = first_mention(haystack, terms)
    if hit:
        return (
            "partial",
            f"Location term '{hit[0]}' mentioned in the resume, but the profile's "
            "location field does not confirm it.",
            [
                Evidence(
                    snippet=hit[1],
                    source="resume_text",
                    match_type="lexical",
                    detail=f"mention of '{hit[0]}'",
                )
            ],
        )
    if not candidate.location:
        return "unknown", "Candidate's location is unknown.", []
    return (
        "missing",
        f"Candidate location '{candidate.location}' does not match the requirement.",
        [],
    )


def _evaluate_domain(
    candidate: Candidate, requirement: JobRequirement, haystack: list[str]
) -> tuple[str, str, list[Evidence]]:
    terms = terms_from_requirement(requirement)
    hits = []
    for term in sorted(terms, key=len, reverse=True):
        hit = first_mention(haystack, [term])
        if hit:
            hits.append(hit)
        if len(hits) >= 2:
            break
    if hits:
        return (
            "met",
            f"Domain evidence found: {', '.join(term for term, _ in hits)}.",
            [
                Evidence(
                    snippet=line,
                    source="resume_text",
                    match_type="lexical",
                    detail=f"mention of '{term}'",
                )
                for term, line in hits
            ],
        )
    return (
        "missing",
        f"No evidence of domain experience ({', '.join(terms[:4]) or 'domain keywords'}).",
        [],
    )


def _evaluate_certification(
    candidate: Candidate, requirement: JobRequirement
) -> tuple[str, str, list[Evidence]]:
    if not candidate.certifications:
        return "missing", "No certifications listed on the profile.", []
    pool = " ".join(f"{cert.name} {cert.issuer or ''}".lower() for cert in candidate.certifications)
    terms = terms_from_requirement(requirement)
    matches = [term for term in terms if _word_in(term, pool)]
    if matches:
        return (
            "met",
            f"Certification matches keyword(s): {', '.join(matches[:3])}.",
            [
                Evidence(
                    snippet=cert.name,
                    source="profile",
                    match_type="lexical",
                    detail="certification entry",
                )
                for cert in candidate.certifications[:1]
            ],
        )
    return "missing", "Listed certifications do not match the requirement.", []


def _evaluate_soft(
    requirement: JobRequirement,
    haystack: list[str],
    candidate_chunks: list,
    embedding_provider: EmbeddingProvider | None,
) -> tuple[str, str, list[Evidence]]:
    evidence: list[Evidence] = []
    similarity = None
    if embedding_provider is not None and candidate_chunks:
        similarity = _label_similarity(requirement.label, candidate_chunks, embedding_provider)
        if similarity is not None and similarity >= SOFT_EVIDENCE_SIMILARITY:
            best_chunk = _best_chunk(requirement, candidate_chunks, embedding_provider)
            if best_chunk:
                evidence.append(
                    Evidence(
                        snippet=best_chunk.chunk_text[:220],
                        source="resume_text",
                        match_type="semantic",
                        detail=f"semantic match (similarity {similarity:.2f})",
                    )
                )
    if not evidence:
        hit = first_mention(haystack, terms_from_requirement(requirement))
        if hit:
            evidence.append(
                Evidence(
                    snippet=hit[1],
                    source="resume_text",
                    match_type="lexical",
                    detail=f"mention of '{hit[0]}'",
                )
            )
    reason = "Soft requirement — shown as a signal for human judgement, not scored."
    if similarity is not None:
        reason += f" Semantic similarity to the profile: {similarity:.2f}."
    return "advisory", reason, evidence


# ── Semantic helpers ────────────────────────────────────────────────────────


def _label_similarity(
    label: str, candidate_chunks: list, provider: EmbeddingProvider
) -> float | None:
    records = [record for record in candidate_chunks if record.embedding]
    if not records:
        return None
    (vector,) = provider.embed([label])
    return round(max(cosine_similarity(vector, record.embedding) for record in records), 4)


def _best_chunk(requirement: JobRequirement, candidate_chunks: list, provider: EmbeddingProvider):
    records = [record for record in candidate_chunks if record.embedding]
    if not records:
        return None
    (vector,) = provider.embed([requirement.label])
    return max(records, key=lambda record: cosine_similarity(vector, record.embedding))


def _overall_similarity(db: Session, candidate_id: int, job_id: int) -> float | None:
    """Mean over job chunks of the best cosine similarity to any candidate chunk."""
    job_chunks = [record for record in get_owner_chunks(db, "job", job_id) if record.embedding]
    candidate_chunks = [
        record for record in get_owner_chunks(db, "candidate", candidate_id) if record.embedding
    ]
    if not job_chunks or not candidate_chunks:
        return None
    job_matrix = _normalized_matrix([record.embedding for record in job_chunks])
    candidate_matrix = _normalized_matrix([record.embedding for record in candidate_chunks])
    similarity_matrix = job_matrix @ candidate_matrix.T
    return round(float(similarity_matrix.max(axis=1).mean()), 4)


def _normalized_matrix(vectors: list[list[float]]) -> np.ndarray:
    matrix = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


# ── Composite scoring (transparent, documented) ─────────────────────────────


def _components(
    evaluations: list[RequirementEvaluation],
) -> tuple[dict[str, float | None], dict[str, float]]:
    def coverage(
        kinds: set[str] | None, categories: set[str] | None, exclude: set[str] | None
    ) -> float | None:
        considered = [
            evaluation
            for evaluation in evaluations
            if evaluation.status in STATUS_SCORES
            and (kinds is None or evaluation.kind in kinds)
            and (categories is None or evaluation.category in categories)
            and (exclude is None or evaluation.category not in exclude)
        ]
        if not considered:
            return None
        return round(sum(STATUS_SCORES[item.status] for item in considered) / len(considered), 4)

    components = {
        "must_have": coverage({"must_have"}, None, _COMPOSITE_EXCLUDED_CATEGORIES),
        "preferred": coverage({"preferred"}, None, _COMPOSITE_EXCLUDED_CATEGORIES),
        "experience": coverage(None, {"experience"}, None),
        "domain": coverage(None, {"domain"}, None),
    }
    present = {name for name, value in components.items() if value is not None}
    total_weight = sum(WEIGHTS[name] for name in present) or 1.0
    weights_used = {name: round(WEIGHTS[name] / total_weight, 4) for name in present}
    return components, weights_used


def _composite(
    components: dict[str, float | None], weights_used: dict[str, float]
) -> tuple[float | None, str]:
    present = {name: value for name, value in components.items() if value is not None}
    if not present:
        return None, "No evaluable requirements for this pair."
    total = sum(weights_used[name] * value for name, value in present.items())
    score = round(100.0 * total, 1)
    parts = " + ".join(
        f"{weights_used[name]:.2f}·{name}[{value:.0%}]" for name, value in present.items()
    )
    formula = f"{parts} = {score:g}/100 (weights re-normalized over present components)"
    return score, formula


def _coverage(evaluations: list[RequirementEvaluation]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for kind in ("must_have", "preferred"):
        subset = [item for item in evaluations if item.kind == kind]
        counts = {status: 0 for status in ("met", "partial", "missing", "unknown", "advisory")}
        for item in subset:
            counts[item.status] += 1
        counts["total"] = len(subset)
        result[kind] = counts
    return result
