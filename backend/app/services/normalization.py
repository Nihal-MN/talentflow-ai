"""Normalization: the last gate before extracted data becomes database truth.

Whatever a provider returns — OpenAI or mock — is normalized here: skills
canonicalized against the shared lexicon, strings cleaned, numbers range-
checked, collections deduplicated. Invalid values are dropped or clamped,
never merely trusted. See ADR 0002/0003.
"""

from __future__ import annotations

import re

from app.ai.base import (
    ExtractedCandidate,
    ExtractedCertification,
    ExtractedEducation,
    ExtractedExperience,
    ExtractedJob,
    ExtractedRequirement,
    ExtractedSkill,
)
from app.services.skills import canonicalize, category_of

VALID_KINDS = {"must_have", "preferred"}
VALID_CATEGORIES = {
    "skill",
    "experience",
    "education",
    "certification",
    "domain",
    "location",
    "other",
}
VALID_EMPLOYMENT_TYPES = {"full_time", "part_time", "contract", "internship"}
VALID_SENIORITIES = {"junior", "mid", "senior", "lead", "principal"}

_MAX_YEARS = 60.0
_MIN_YEAR = 1950
_MAX_YEAR = 2035


def clean_text(value: object, *, max_len: int = 2000) -> str | None:
    """Collapse whitespace, strip, cap length; empty → ``None``."""
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text[:max_len] or None


def _clean_email(value: object) -> str | None:
    text = clean_text(value, max_len=320)
    if not text:
        return None
    text = text.strip("<>").lower()
    if re.fullmatch(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", text):
        return text
    return None


def _clean_url(value: object) -> str | None:
    text = clean_text(value, max_len=500)
    if not text:
        return None
    if not text.lower().startswith(("http://", "https://")):
        text = "https://" + text
    return text


def _clamp_years(value: float | None) -> float | None:
    if value is None:
        return None
    if value < 0 or value > _MAX_YEARS:
        return None
    return round(float(value), 1)


def _clamp_year(value: int | None) -> int | None:
    if value is None or value < _MIN_YEAR or value > _MAX_YEAR:
        return None
    return int(value)


def normalize_skill(
    raw_name: str,
    raw_category: str | None = None,
    *,
    normalized_hint: str | None = None,
    evidence: str | None = None,
) -> ExtractedSkill | None:
    """Canonicalize a skill mention; returns ``None`` for empty noise."""
    name = clean_text(raw_name, max_len=120)
    if not name or len(name) < 2:
        return None
    canonical = canonicalize(normalized_hint or name)
    normalized = canonical or (normalized_hint or name).lower()
    category = (
        category_of(canonical)
        if canonical
        else ((raw_category or "other").strip().lower() or "other")
    )
    if category not in {
        "language",
        "framework",
        "database",
        "cloud",
        "devops",
        "data",
        "testing",
        "ai",
        "analytics",
        "tool",
        "soft",
        "other",
    }:
        category = "other"
    return ExtractedSkill(
        name=name,
        normalized_name=normalized,
        category=category,
        evidence=clean_text(evidence, max_len=300),
    )


def normalize_candidate(extracted: ExtractedCandidate) -> ExtractedCandidate:
    """Return a cleaned, deduplicated, range-checked candidate profile."""
    experiences: list[ExtractedExperience] = []
    seen_roles: set[tuple] = set()
    for experience in extracted.experiences[:30]:
        title = clean_text(experience.title, max_len=200)
        company = clean_text(experience.company, max_len=200)
        if not title and not company and experience.start_date is None:
            continue
        key = (title, company, experience.start_date)
        if key in seen_roles:
            continue
        seen_roles.add(key)
        start, end = experience.start_date, experience.end_date
        is_current = bool(experience.is_current)
        if start and end and end < start:
            end = None  # inconsistent range; keep the start date only
        experiences.append(
            ExtractedExperience(
                company=company,
                title=title,
                location=clean_text(experience.location, max_len=200),
                start_date=start,
                end_date=None if is_current else end,
                is_current=is_current or (start is not None and end is None),
                description=clean_text(experience.description, max_len=6000),
            )
        )

    educations: list[ExtractedEducation] = []
    seen_education: set[tuple] = set()
    for education in extracted.educations[:10]:
        institution = clean_text(education.institution, max_len=300)
        degree = clean_text(education.degree, max_len=200)
        if not institution and not degree:
            continue
        key = (degree, institution, education.end_year)
        if key in seen_education:
            continue
        seen_education.add(key)
        start_year, end_year = _clamp_year(education.start_year), _clamp_year(education.end_year)
        if start_year and end_year and end_year < start_year:
            start_year, end_year = end_year, start_year
        educations.append(
            ExtractedEducation(
                institution=institution,
                degree=degree,
                field_of_study=clean_text(education.field_of_study, max_len=200),
                start_year=start_year,
                end_year=end_year,
            )
        )

    skills: list[ExtractedSkill] = []
    seen_skills: set[str] = set()
    for skill in extracted.skills:
        cleaned = normalize_skill(
            skill.normalized_name or skill.name,
            skill.category,
            normalized_hint=skill.normalized_name,
            evidence=skill.evidence,
        )
        if cleaned is None or cleaned.normalized_name in seen_skills:
            continue
        seen_skills.add(cleaned.normalized_name)
        skills.append(cleaned)

    certifications: list[ExtractedCertification] = []
    seen_certs: set[str] = set()
    for certification in extracted.certifications[:20]:
        name = clean_text(certification.name, max_len=200)
        if not name or name.lower() in seen_certs:
            continue
        seen_certs.add(name.lower())
        certifications.append(
            ExtractedCertification(
                name=name,
                issuer=clean_text(certification.issuer, max_len=200),
                year=_clamp_year(certification.year),
            )
        )

    return ExtractedCandidate(
        full_name=clean_text(extracted.full_name, max_len=200) or "Unknown Candidate",
        email=_clean_email(extracted.email),
        phone=clean_text(extracted.phone, max_len=50),
        location=clean_text(extracted.location, max_len=200),
        headline=clean_text(extracted.headline, max_len=300),
        summary=clean_text(extracted.summary, max_len=4000),
        years_experience=_clamp_years(extracted.years_experience),
        linkedin_url=_clean_url(extracted.linkedin_url),
        github_url=_clean_url(extracted.github_url),
        website_url=_clean_url(extracted.website_url),
        experiences=experiences,
        educations=educations,
        skills=skills,
        certifications=certifications,
    )


def normalize_job(extracted: ExtractedJob) -> ExtractedJob:
    """Return a cleaned, validated job + requirements."""
    requirements: list[ExtractedRequirement] = []
    seen: set[tuple] = set()
    for requirement in extracted.requirements[:60]:
        label = clean_text(requirement.label, max_len=300)
        if not label:
            continue
        kind = requirement.kind if requirement.kind in VALID_KINDS else "must_have"
        category = requirement.category if requirement.category in VALID_CATEGORIES else "other"
        normalized_skill = clean_text(requirement.normalized_skill, max_len=120)
        normalized_skill = normalized_skill.lower() if normalized_skill else None
        if category == "skill" and not normalized_skill:
            canonical = canonicalize(label)
            normalized_skill = canonical
        key = (category, normalized_skill or label.lower())
        if key in seen:
            continue
        seen.add(key)
        keywords = []
        for keyword in requirement.keywords[:6]:
            cleaned = clean_text(keyword, max_len=40)
            if cleaned and cleaned.lower() not in [k.lower() for k in keywords]:
                keywords.append(cleaned.lower())
        min_years = requirement.min_years
        if min_years is not None and (min_years < 0 or min_years > 50):
            min_years = None
        requirements.append(
            ExtractedRequirement(
                kind=kind,
                category=category,
                label=label,
                normalized_skill=normalized_skill,
                min_years=min_years,
                keywords=keywords,
            )
        )

    employment_type = (extracted.employment_type or "").strip().lower()
    seniority = (extracted.seniority or "").strip().lower()
    return ExtractedJob(
        title=clean_text(extracted.title, max_len=200) or "Untitled role",
        company=clean_text(extracted.company, max_len=200) or "",
        location=clean_text(extracted.location, max_len=200),
        employment_type=employment_type
        if employment_type in VALID_EMPLOYMENT_TYPES
        else "full_time",
        seniority=seniority if seniority in VALID_SENIORITIES else None,
        domain=(clean_text(extracted.domain, max_len=80) or None),
        summary=clean_text(extracted.summary, max_len=4000),
        requirements=requirements,
    )
