"""Mock provider (deterministic extraction) unit tests."""

from __future__ import annotations

from app.ai.mock_provider import MOCK_MODEL_NAME, MockLLMProvider
from app.seed.demo_jobs import DEMO_JOBS

PROVIDER = MockLLMProvider()

JD = DEMO_JOBS["senior-full-stack-engineer"]["text"]

RESUME = """\
Jordan Lee
Backend Developer
Berlin, Germany
jordan.lee@example.com | +49 30 555 0199 | github.com/jordanlee

Summary
Backend developer with 6 years of experience building data platforms.

Experience
Senior Backend Developer — DataForge GmbH (Berlin, Germany)
Apr 2021 – Present
- Built streaming pipelines in Python and Kafka
- Worked with PostgreSQL and Docker daily

Backend Developer — Bluewave Systems (Remote)
Jan 2019 – Mar 2021
- Developed REST APIs in JS and Node.js

Education
MSc Computer Science — TU Berlin (2016 – 2018)

Skills
Python, JS, PostgreSQL, Docker, Kafka, Git
"""


def test_extract_job_splits_must_have_and_preferred():
    job = PROVIDER.extract_job(JD)

    assert job.title == "Senior Full Stack Engineer"
    assert job.seniority == "senior"
    assert job.location == "Dubai"
    assert job.domain == "logistics"

    must_skills = [r.normalized_skill for r in job.requirements if r.kind == "must_have"]
    pref_skills = [r.normalized_skill for r in job.requirements if r.kind == "preferred"]

    assert "python" in must_skills and "react" in must_skills
    assert "kubernetes" in pref_skills
    assert "kubernetes" not in must_skills  # "Nice to have" section not detected = bug


def test_extract_job_detects_years_and_degree():
    job = PROVIDER.extract_job(JD)
    years = [r for r in job.requirements if r.category == "experience"]
    assert years and years[0].min_years == 5.0
    assert any(r.category == "education" for r in job.requirements)


def test_extract_job_remote_is_not_mistaken_for_rome():
    jd = "DevOps Engineer\n\nRequirements\n- 4+ years of experience\n- Kubernetes\nLocation: Remote (UTC+4 preferred)\n"
    job = PROVIDER.extract_job(jd)
    assert job.location == "Remote"


def test_extract_job_ignores_prose_paragraphs():
    jd = (
        "Data Analyst\n\nAbout the role\n"
        "We use Python and React across the company and we love our PostgreSQL stack deeply.\n\n"
        "Requirements\n- 3+ years of experience\n- SQL\n"
    )
    job = PROVIDER.extract_job(jd)
    skills = {r.normalized_skill for r in job.requirements}
    assert "sql" in skills
    # The prose paragraph must not become a requirement.
    assert "react" not in skills and "postgresql" not in skills


def test_extract_candidate_parses_core_fields():
    candidate = PROVIDER.extract_candidate(RESUME, source_filename="jordan_lee.txt")

    assert candidate.full_name == "Jordan Lee"
    assert candidate.email == "jordan.lee@example.com"
    assert candidate.phone and candidate.phone.endswith("0199")
    assert candidate.location == "Berlin, Germany"
    assert candidate.github_url and "jordanlee" in candidate.github_url

    assert len(candidate.experiences) == 2
    current = candidate.experiences[0]
    assert current.company == "DataForge GmbH"
    assert current.title == "Senior Backend Developer"
    assert current.is_current is True
    assert current.end_date is None

    assert candidate.years_experience and candidate.years_experience > 6

    assert candidate.educations and "TU Berlin" in (candidate.educations[0].institution or "") + (
        candidate.educations[0].degree or ""
    )


def test_extract_candidate_canonicalizes_skill_aliases():
    candidate = PROVIDER.extract_candidate(RESUME)
    skills = {s.normalized_name for s in candidate.skills}
    assert "javascript" in skills  # "JS" alias
    assert "python" in skills
    assert "postgresql" in skills


def test_mock_provider_is_deterministic():
    first = PROVIDER.extract_job(JD)
    second = PROVIDER.extract_job(JD)
    assert first.requirements == second.requirements
    assert first.title == second.title

    r1 = PROVIDER.extract_candidate(RESUME)
    r2 = PROVIDER.extract_candidate(RESUME)
    assert r1 == r2
    assert PROVIDER.model == MOCK_MODEL_NAME


def test_screening_questions_cover_gaps_and_strengths():
    questions = PROVIDER.generate_screening_questions(
        job_title="Senior Full Stack Engineer",
        candidate_name="Amira Haddad",
        years_experience=8.2,
        matched_skills=["python", "react"],
        missing_skills=["kubernetes"],
        seniority="senior",
    )
    categories = {q.category for q in questions}
    assert {"technical", "gap_probe", "experience", "behavioral"} <= categories
    assert any("kubernetes" in q.question for q in questions)
    assert any(q.rationale for q in questions)
    assert len(questions) <= 7
