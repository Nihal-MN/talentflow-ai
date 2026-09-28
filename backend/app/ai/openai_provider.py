"""OpenAI implementation of the AI provider interfaces.

Uses the current Responses API with Structured Outputs
(``client.responses.parse(..., text_format=PydanticModel)``), so every response
is schema-validated before it ever reaches the services layer. The client is
injectable so the wiring can be unit-tested without network access.
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai import prompts, schemas
from app.ai.base import (
    ExtractedCandidate,
    ExtractedCertification,
    ExtractedEducation,
    ExtractedExperience,
    ExtractedJob,
    ExtractedRequirement,
    ExtractedSkill,
    ScreeningQuestionDraft,
)
from app.core.dates import compute_years_experience, parse_partial_date
from app.core.errors import ProviderUnavailableError

logger = logging.getLogger(__name__)

#: Cap on document characters sent to the model (defensive, keeps costs sane).
MAX_DOCUMENT_CHARS = 60_000


class OpenAILLMProvider:
    """LLM provider backed by the OpenAI API (Responses + structured outputs)."""

    name = "openai"

    def __init__(
        self,
        *,
        api_key: str = "",
        model: str,
        embedding_model: str,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.embedding_model = embedding_model
        if client is not None:
            self._client = client  # injected (tests) — no key required
            return
        if not api_key:
            raise ProviderUnavailableError("OPENAI_API_KEY is not set")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency is pinned
            raise ProviderUnavailableError("The 'openai' package is not installed") from exc
        self._client = OpenAI(api_key=api_key)

    # ── LLMProvider interface ────────────────────────────────────────────────

    def extract_job(self, jd_text: str) -> ExtractedJob:
        parsed = self._parse(
            system=prompts.JD_SYSTEM_PROMPT,
            user=prompts.JD_USER_TEMPLATE.format(jd_text=jd_text[:MAX_DOCUMENT_CHARS]),
            response_model=schemas.JobExtractionModel,
        )
        return _to_extracted_job(parsed)

    def extract_candidate(
        self, resume_text: str, *, source_filename: str | None = None
    ) -> ExtractedCandidate:
        parsed = self._parse(
            system=prompts.RESUME_SYSTEM_PROMPT,
            user=prompts.RESUME_USER_TEMPLATE.format(
                filename=source_filename or "resume", resume_text=resume_text[:MAX_DOCUMENT_CHARS]
            ),
            response_model=schemas.CandidateExtractionModel,
        )
        return _to_extracted_candidate(parsed)

    def generate_screening_questions(
        self,
        *,
        job_title: str,
        candidate_name: str,
        years_experience: float | None,
        matched_skills: list[str],
        missing_skills: list[str],
        seniority: str | None,
    ) -> list[ScreeningQuestionDraft]:
        parsed = self._parse(
            system=prompts.SCREENING_SYSTEM_PROMPT,
            user=prompts.SCREENING_USER_TEMPLATE.format(
                job_title=job_title,
                seniority=seniority or "unspecified",
                must_have_skills=", ".join(matched_skills + missing_skills) or "n/a",
                preferred_skills="see requirements",
                candidate_name=candidate_name,
                years_experience=years_experience if years_experience is not None else "unknown",
                matched_skills=", ".join(matched_skills) or "none",
                missing_skills=", ".join(missing_skills) or "none",
            ),
            response_model=schemas.ScreeningQuestionsModel,
        )
        return [
            ScreeningQuestionDraft(
                category=question.category,
                question=question.question,
                rationale=question.rationale,
            )
            for question in parsed.questions
        ]

    # ── internals ────────────────────────────────────────────────────────────

    def _parse(self, *, system: str, user: str, response_model: Any) -> Any:
        try:
            response = self._client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                text_format=response_model,
            )
        except Exception as exc:
            logger.warning("OpenAI request failed: %s", exc)
            raise ProviderUnavailableError(f"OpenAI request failed: {exc}") from exc
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise ProviderUnavailableError("OpenAI returned no structured output")
        return parsed


# ── Schema → value-object conversion ────────────────────────────────────────


def _to_extracted_job(model: schemas.JobExtractionModel) -> ExtractedJob:
    return ExtractedJob(
        title=model.title.strip(),
        company=(model.company or "").strip() or None,
        location=(model.location or "").strip() or None,
        employment_type=(model.employment_type or "").strip() or None,
        seniority=(model.seniority or "").strip().lower() or None,
        domain=(model.domain or "").strip().lower() or None,
        summary=(model.summary or "").strip() or None,
        requirements=[
            ExtractedRequirement(
                kind=req.kind if req.kind in ("must_have", "preferred") else "must_have",
                category=req.category,
                label=req.label.strip(),
                normalized_skill=(req.normalized_skill or "").strip().lower() or None,
                min_years=req.min_years,
                keywords=[keyword.strip().lower() for keyword in req.keywords if keyword.strip()],
            )
            for req in model.requirements
            if req.label.strip()
        ],
    )


def _to_extracted_candidate(model: schemas.CandidateExtractionModel) -> ExtractedCandidate:
    experiences = [
        ExtractedExperience(
            company=(exp.company or "").strip() or None,
            title=(exp.title or "").strip() or None,
            location=(exp.location or "").strip() or None,
            start_date=parse_partial_date(exp.start_date),
            end_date=None if exp.is_current else parse_partial_date(exp.end_date),
            is_current=exp.is_current or (exp.end_date is None and exp.start_date is not None),
            description=(exp.description or "").strip() or None,
        )
        for exp in model.experiences
    ]
    years = (
        model.years_experience
        if model.years_experience is not None
        else compute_years_experience(experiences)
    )
    return ExtractedCandidate(
        full_name=model.full_name.strip(),
        email=(model.email or "").strip() or None,
        phone=(model.phone or "").strip() or None,
        location=(model.location or "").strip() or None,
        headline=(model.headline or "").strip() or None,
        summary=(model.summary or "").strip() or None,
        years_experience=years,
        linkedin_url=(model.linkedin_url or "").strip() or None,
        github_url=(model.github_url or "").strip() or None,
        website_url=(model.website_url or "").strip() or None,
        experiences=experiences,
        educations=[
            ExtractedEducation(
                institution=(edu.institution or "").strip() or None,
                degree=(edu.degree or "").strip() or None,
                field_of_study=(edu.field_of_study or "").strip() or None,
                start_year=edu.start_year,
                end_year=edu.end_year,
            )
            for edu in model.educations
        ],
        skills=[
            ExtractedSkill(
                name=skill.name.strip(),
                normalized_name=(skill.normalized_name or skill.name).strip().lower(),
                category=(skill.category or "other").strip().lower(),
                evidence=(skill.evidence or "").strip() or None,
            )
            for skill in model.skills
            if skill.name.strip()
        ],
        certifications=[
            ExtractedCertification(
                name=cert.name.strip(),
                issuer=(cert.issuer or "").strip() or None,
                year=cert.year,
            )
            for cert in model.certifications
        ],
    )
