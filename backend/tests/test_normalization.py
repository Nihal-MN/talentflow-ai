"""Normalization + skill-taxonomy unit tests."""

from __future__ import annotations

from datetime import date

from app.ai.base import (
    ExtractedCandidate,
    ExtractedExperience,
    ExtractedJob,
    ExtractedRequirement,
    ExtractedSkill,
)
from app.services.normalization import clean_text, normalize_candidate, normalize_job
from app.services.skills import are_related, canonicalize, category_of, extract_skills

# ── Skill taxonomy ──────────────────────────────────────────────────────────


def test_canonicalize_aliases():
    assert canonicalize("JS") == "javascript"
    assert canonicalize("  React.js ") == "react"
    assert canonicalize("Postgres") == "postgresql"
    assert canonicalize("k8s") == "kubernetes"
    assert canonicalize("node") == "node.js"
    assert canonicalize("totally-unknown-thing") is None


def test_categories_and_relatedness():
    assert category_of("python") == "language"
    assert category_of("postgresql") == "database"
    assert are_related("docker", "kubernetes") is True
    assert are_related("docker", "python") is False
    assert are_related("react", "react") is False  # identical is not "related"


def test_extract_skills_finds_evidence_lines():
    text = "Led migration to Python and FastAPI.\nOwned the PostgreSQL schema design."
    hits = {hit.canonical: hit for hit in extract_skills(text)}
    assert "python" in hits and "postgresql" in hits
    assert "FastAPI" in hits["fastapi"].evidence


def test_extract_skills_avoids_substring_false_positives():
    hits = {hit.canonical for hit in extract_skills("Great communication with customers.")}
    assert "go" not in hits  # not even a defined skill — sanity
    assert "java" not in hits  # 'java' must not match inside 'javascript'-free text


def test_js_alias_does_not_fire_inside_compound_names():
    """Regression: 'Node.js' must yield node.js — and NOT a phantom 'javascript'."""
    hits = {hit.canonical for hit in extract_skills("Expert-level Node.js development")}
    assert "node.js" in hits
    assert "javascript" not in hits

    hits = {hit.canonical for hit in extract_skills("Vue.js and Next.js experience")}
    assert "vue" in hits and "next.js" in hits
    assert "javascript" not in hits

    # A standalone "JS" mention still counts.
    assert "javascript" in {hit.canonical for hit in extract_skills("Strong JS skills")}


# ── Normalization ───────────────────────────────────────────────────────────


def test_clean_text_collapses_and_caps():
    assert clean_text("  a\n\n  b  ") == "a b"
    assert clean_text("") is None
    assert len(clean_text("x" * 5000, max_len=100)) == 100


def test_normalize_candidate_dedupes_and_validates():
    extracted = ExtractedCandidate(
        full_name="  Jane   Doe ",
        email="JANE@Example.com",
        years_experience=200.0,  # absurd → dropped
        experiences=[
            ExtractedExperience(
                company="A",
                title="Dev",
                start_date=date(2024, 6, 1),
                end_date=date(2021, 1, 1),
                is_current=True,
            ),
            ExtractedExperience(
                company="A",
                title="Dev",
                start_date=date(2024, 6, 1),
                end_date=date(2021, 1, 1),
                is_current=True,
            ),  # dupe
        ],
        skills=[
            ExtractedSkill(name="JS", normalized_name="js", category="language"),
            ExtractedSkill(
                name="JavaScript", normalized_name="javascript", category="language"
            ),  # dupe after canonicalization
            ExtractedSkill(name="", normalized_name="", category="other"),  # noise → dropped
        ],
    )
    cleaned = normalize_candidate(extracted)

    assert cleaned.full_name == "Jane Doe"
    assert cleaned.email == "jane@example.com"
    assert cleaned.years_experience is None
    assert len(cleaned.experiences) == 1
    # Inconsistent date range: end dropped, current retained.
    assert cleaned.experiences[0].end_date is None

    names = [s.normalized_name for s in cleaned.skills]
    assert names == ["javascript"]  # deduped via alias canonicalization


def test_normalize_job_validates_kinds_and_dedupes():
    extracted = ExtractedJob(
        title="  Data Analyst  ",
        employment_type="FULL_TIME",
        seniority="MID",
        requirements=[
            ExtractedRequirement(
                kind="bogus", category="skill", label="SQL", normalized_skill="SQL"
            ),
            ExtractedRequirement(
                kind="must_have", category="skill", label="SQL again", normalized_skill="sql"
            ),  # dupe
            ExtractedRequirement(
                kind="preferred", category="wrong", label=" ", normalized_skill=None
            ),  # empty label → dropped
            ExtractedRequirement(
                kind="preferred", category="experience", label="3+ years", min_years=99.0
            ),  # clamped
        ],
    )
    cleaned = normalize_job(extracted)

    assert cleaned.title == "Data Analyst"
    assert cleaned.employment_type == "full_time"
    assert cleaned.seniority == "mid"
    assert len(cleaned.requirements) == 2
    assert cleaned.requirements[0].kind == "must_have"  # invalid kind fixed
    assert cleaned.requirements[0].normalized_skill == "sql"
    assert cleaned.requirements[1].min_years is None  # 99 → implausible → dropped
    assert cleaned.requirements[1].category == "experience"
    assert cleaned.requirements[1].label == "3+ years"


def test_normalize_candidate_keeps_skill_evidence():
    extracted = ExtractedCandidate(
        full_name="E",
        skills=[
            ExtractedSkill(
                name="Python",
                normalized_name="python",
                category="language",
                evidence="  Built pipelines in Python. ",
            )
        ],
    )
    cleaned = normalize_candidate(extracted)
    assert cleaned.skills[0].evidence == "Built pipelines in Python."
