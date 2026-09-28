"""Deterministic offline mock of the LLM provider.

Same input → same output, no network, no API key. Used when
``AI_PROVIDER=mock`` (or ``auto`` without a key) so the product, the demo and
the test suite run anywhere. Everything produced here is labeled ``mock`` in
API responses and in the System Health page — it is never presented as model
output. See docs/adr/0002.
"""

from __future__ import annotations

from app.ai.base import (
    ExtractedCandidate,
    ExtractedJob,
    ScreeningQuestionDraft,
)
from app.ai.mock_jd import parse_job
from app.ai.mock_resume import parse_resume

#: Bump when parsing rules change; stored as `extraction_model` provenance.
MOCK_MODEL_NAME = "deterministic-rules-v1"


class MockLLMProvider:
    """Rule-based implementation of ``LLMProvider`` (offline, deterministic)."""

    name = "mock"
    model = MOCK_MODEL_NAME

    def extract_job(self, jd_text: str) -> ExtractedJob:
        return parse_job(jd_text)

    def extract_candidate(
        self, resume_text: str, *, source_filename: str | None = None
    ) -> ExtractedCandidate:
        return parse_resume(resume_text, source_filename=source_filename)

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
        questions: list[ScreeningQuestionDraft] = []

        for skill in matched_skills[:3]:
            questions.append(
                ScreeningQuestionDraft(
                    category="technical",
                    question=(
                        f"Walk me through a project where you used {skill} in production — "
                        "what did you build, and what trade-offs did you make?"
                    ),
                    rationale=(
                        f"Verifies depth in {skill}, one of the candidate's strongest "
                        f"matches for {job_title}."
                    ),
                )
            )

        for skill in missing_skills[:3]:
            questions.append(
                ScreeningQuestionDraft(
                    category="gap_probe",
                    question=(
                        f"Our {job_title} role relies on {skill}, which isn't visible in "
                        "your profile yet. How would you come up to speed on it in your "
                        "first 30 days?"
                    ),
                    rationale=(
                        f"Honest gap probe for the required skill '{skill}' before "
                        "investing further."
                    ),
                )
            )

        if years_experience is not None:
            questions.append(
                ScreeningQuestionDraft(
                    category="experience",
                    question=(
                        f"You bring roughly {years_experience:g} years of experience — "
                        f"which of your roles best prepared you for the day-to-day of "
                        f"this {job_title} position, and why?"
                    ),
                    rationale="Connects the candidate's trajectory to this specific role scope.",
                )
            )

        if seniority in ("senior", "lead", "principal"):
            questions.append(
                ScreeningQuestionDraft(
                    category="behavioral",
                    question=(
                        "Tell me about a time you drove a significant technical decision "
                        "that others initially disagreed with — how did you build agreement?"
                    ),
                    rationale=(
                        "Senior roles require influencing and leadership beyond pure "
                        "implementation."
                    ),
                )
            )
        else:
            questions.append(
                ScreeningQuestionDraft(
                    category="behavioral",
                    question=(
                        "Describe a piece of feedback that changed how you work — what "
                        "did you do differently afterwards?"
                    ),
                    rationale=(
                        "Signals coachability and self-awareness, important at this career stage."
                    ),
                )
            )

        if not matched_skills and not missing_skills:
            questions.append(
                ScreeningQuestionDraft(
                    category="experience",
                    question=(
                        f"What interests you specifically about this {job_title} position, "
                        "and which parts of your background map most closely to it?"
                    ),
                    rationale="Opening question when skill overlap is still being established.",
                )
            )

        return questions[:7]
