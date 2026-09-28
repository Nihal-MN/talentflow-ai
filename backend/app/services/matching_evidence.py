"""Evidence retrieval helpers for the matching engine.

Evidence must always be traceable: snippets are quoted verbatim from the
candidate's own resume text (or structured profile when no raw text exists),
together with where they came from and how they were found. No generated or
paraphrased "evidence" is ever presented as source material.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.job import JobRequirement

_STOPWORDS = {
    "and",
    "or",
    "the",
    "a",
    "an",
    "of",
    "for",
    "with",
    "in",
    "on",
    "to",
    "at",
    "experience",
    "strong",
    "good",
    "excellent",
    "years",
    "year",
    "work",
    "working",
    "skills",
    "skill",
    "knowledge",
    "proven",
    "ability",
    "plus",
    "nice",
    "have",
    "must",
    "required",
    "preferred",
    "using",
    "used",
}


def candidate_haystack(candidate: Candidate) -> list[str]:
    """Lines used for evidence search: raw resume text first, then structure."""
    lines: list[str] = []
    if candidate.resume_text:
        lines.extend(line.strip() for line in candidate.resume_text.splitlines() if line.strip())
    if candidate.headline:
        lines.append(candidate.headline)
    if candidate.summary:
        lines.extend(
            segment.strip()
            for segment in re.split(r"(?<=[.!?])\s+", candidate.summary)
            if segment.strip()
        )
    for experience in candidate.experiences:
        heading = " at ".join(part for part in [experience.title, experience.company] if part)
        if heading:
            lines.append(heading)
        if experience.description:
            lines.extend(
                line.strip(" -•") for line in experience.description.splitlines() if line.strip()
            )
    for skill in candidate.skills:
        if skill.evidence:
            lines.append(skill.evidence)
    for education in candidate.educations:
        combined = " — ".join(part for part in [education.degree, education.institution] if part)
        if combined:
            lines.append(combined)
    # De-duplicate while preserving order.
    seen: set[str] = set()
    unique: list[str] = []
    for line in lines:
        key = line.lower()
        if key not in seen:
            seen.add(key)
            unique.append(line)
    return unique


def terms_from_requirement(requirement: JobRequirement) -> list[str]:
    """Search terms for a requirement: skill, keywords, then label words."""
    terms: list[str] = []
    if requirement.normalized_skill:
        terms.append(requirement.normalized_skill)
    for keyword in (requirement.keywords or "").split(","):
        keyword = keyword.strip().lower()
        if keyword and keyword not in terms:
            terms.append(keyword)
    if not terms:
        for word in re.findall(r"[A-Za-z][A-Za-z+#.\-]{2,}", requirement.label.lower()):
            if word not in _STOPWORDS and word not in terms:
                terms.append(word)
    return terms[:8]


def _term_regex(term: str) -> re.Pattern[str]:
    """Word-bounded term pattern; a preceding dot is rejected so short terms
    like ``js`` can't match inside "Node.js" (mirrors the skill lexicon)."""
    escaped = re.escape(term).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![A-Za-z0-9+#.]){escaped}(?![A-Za-z0-9+#])", re.IGNORECASE)


def find_evidence_lines(
    lines: list[str], terms: list[str], *, limit: int = 2, max_chars: int = 220
) -> list[tuple[str, str]]:
    """Return up to ``limit`` (term, line) hits, longest terms first."""
    hits: list[tuple[str, str]] = []
    for term in sorted(terms, key=len, reverse=True):
        if len(hits) >= limit:
            break
        pattern = _term_regex(term)
        for line in lines:
            if len(line) > 400:
                continue
            if pattern.search(line):
                hits.append((term, line[:max_chars]))
                break
    return hits


def first_mention(lines: list[str], terms: list[str]) -> tuple[str, str] | None:
    """Single best (term, line) hit, or ``None``."""
    hits = find_evidence_lines(lines, terms, limit=1)
    return hits[0] if hits else None
