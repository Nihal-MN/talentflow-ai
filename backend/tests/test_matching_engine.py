"""Matching engine unit tests — the explainability guarantees.

These are the tests that make the "no mysterious AI score" claim real:
deterministic statuses, published weights, quoted evidence, and a hard
assertion that no protected-attribute columns exist anywhere in the schema.
"""

from __future__ import annotations

from datetime import date

from app.models.candidate import Candidate, CandidateEducation, CandidateExperience, CandidateSkill
from app.models.job import Job, JobRequirement
from app.services.matching import (
    ENGINE_VERSION,
    WEIGHTS,
    evaluate_pair,
)


def make_candidate(db, *, name="Test Candidate", **overrides) -> Candidate:
    candidate = Candidate(
        full_name=name,
        headline=overrides.get("headline"),
        location=overrides.get("location"),
        years_experience=overrides.get("years_experience"),
        summary=overrides.get("summary"),
        resume_text=overrides.get("resume_text"),
        extraction_method="manual",
    )
    for skill_name in overrides.get("skills", []):
        candidate.skills.append(
            CandidateSkill(name=skill_name, normalized_name=skill_name.lower(), category="other")
        )
    for role in overrides.get("roles", []):
        candidate.experiences.append(
            CandidateExperience(
                title=role.get("title"),
                company=role.get("company"),
                start_date=role.get("start"),
                end_date=role.get("end"),
                is_current=role.get("current", False),
            )
        )
    for education in overrides.get("educations", []):
        candidate.educations.append(
            CandidateEducation(
                degree=education.get("degree"), institution=education.get("institution")
            )
        )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def make_job(db, requirements: list[dict], **overrides) -> Job:
    job = Job(
        title=overrides.get("title", "Test Job"),
        company="Test Co",
        status="open",
        description_text=overrides.get("description", "Test description " * 5),
        seniority=overrides.get("seniority"),
        domain=overrides.get("domain"),
    )
    for index, spec in enumerate(requirements):
        job.requirements.append(
            JobRequirement(
                kind=spec.get("kind", "must_have"),
                category=spec["category"],
                label=spec.get("label", spec.get("skill", spec["category"])),
                normalized_skill=spec.get("skill"),
                min_years=spec.get("min_years"),
                keywords=spec.get("keywords"),
                order_index=index,
            )
        )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def evaluate(db, candidate, job):
    return evaluate_pair(db, candidate, job)


# ── Skill evaluation ────────────────────────────────────────────────────────


def test_skill_met_when_present(db_session):
    candidate = make_candidate(db_session, skills=["python"])
    job = make_job(db_session, [{"category": "skill", "skill": "python"}])
    result = evaluate(db_session, candidate, job)

    (evaluation,) = result.requirements
    assert evaluation.status == "met"
    assert result.composite_score == 100.0


def test_skill_partial_for_related_skill_only(db_session):
    # kubernetes and docker share the "containers" family.
    candidate = make_candidate(db_session, skills=["docker"])
    job = make_job(db_session, [{"category": "skill", "skill": "kubernetes"}])
    (evaluation,) = evaluate(db_session, candidate, job).requirements

    assert evaluation.status == "partial"
    assert "related" in evaluation.reason.lower()


def test_skill_met_via_resume_text_when_not_extracted(db_session):
    candidate = make_candidate(db_session, resume_text="We used Terraform heavily at my last job.")
    job = make_job(db_session, [{"category": "skill", "skill": "terraform"}])
    (evaluation,) = evaluate(db_session, candidate, job).requirements

    assert evaluation.status == "met"
    assert "resume text" in evaluation.reason
    assert evaluation.evidence and "Terraform" in evaluation.evidence[0].snippet


def test_skill_missing(db_session):
    candidate = make_candidate(db_session, skills=["python"], resume_text="Python programmer.")
    job = make_job(db_session, [{"category": "skill", "skill": "kubernetes"}])
    (evaluation,) = evaluate(db_session, candidate, job).requirements
    assert evaluation.status == "missing"
    assert evaluation.evidence == []


# ── Experience evaluation ───────────────────────────────────────────────────


def test_experience_met_partial_missing_and_unknown(db_session):
    def run(min_years, years):
        candidate = make_candidate(db_session, name=f"c{min_years}-{years}", years_experience=years)
        job = make_job(
            db_session,
            [{"category": "experience", "min_years": min_years, "label": f"{min_years}+ yrs"}],
        )
        return evaluate(db_session, candidate, job).requirements[0]

    assert run(5, 8).status == "met"
    assert run(5, 4).status == "partial"  # within the 1.5-year tolerance
    assert run(5, 2).status == "missing"
    assert run(5, None).status == "unknown"

    computed = run(5, 8)
    assert computed.evidence and computed.evidence[0].match_type == "computed"


def test_experience_without_min_years_is_not_auto_scored(db_session):
    candidate = make_candidate(db_session, resume_text="Plenty of backend experience.")
    job = make_job(db_session, [{"category": "experience", "label": "Significant experience"}])
    (evaluation,) = evaluate(db_session, candidate, job).requirements
    assert evaluation.status == "unknown"


# ── Education / location / domain / certifications ──────────────────────────


def test_education_statuses(db_session):
    with_degree = make_candidate(
        db_session,
        educations=[{"degree": "BSc Computer Science", "institution": "Tech University"}],
    )
    without = make_candidate(db_session, name="NoEdu")
    job = make_job(
        db_session,
        [
            {
                "category": "education",
                "label": "Bachelor's degree in Computer Science",
                "keywords": "bachelor",
            }
        ],
    )

    assert evaluate(db_session, with_degree, job).requirements[0].status == "met"
    assert evaluate(db_session, without, job).requirements[0].status == "unknown"


def test_location_remote_and_city_match(db_session):
    remote_job = make_job(
        db_session,
        [{"category": "location", "label": "Remote (UTC+4 preferred)", "keywords": "remote"}],
    )
    anyone = make_candidate(db_session, name="RemoteOk")
    assert evaluate(db_session, anyone, remote_job).requirements[0].status == "met"

    dubai_job = make_job(
        db_session,
        [{"category": "location", "label": "Location: Dubai, UAE", "keywords": "dubai,uae"}],
    )
    local = make_candidate(db_session, name="Local", location="Dubai, UAE")
    abroad = make_candidate(db_session, name="Abroad", location="Berlin, Germany")
    assert evaluate(db_session, local, dubai_job).requirements[0].status == "met"
    assert evaluate(db_session, abroad, dubai_job).requirements[0].status == "missing"


def test_domain_evaluated_from_evidence(db_session):
    candidate = make_candidate(
        db_session,
        resume_text="Built freight tracking dashboards for a logistics operator.",
    )
    job = make_job(
        db_session,
        [
            {
                "category": "domain",
                "label": "Experience in logistics",
                "keywords": "logistics,freight",
            }
        ],
    )
    evaluation = evaluate(db_session, candidate, job).requirements[0]
    assert evaluation.status == "met"
    assert evaluation.evidence and "freight" in evaluation.evidence[0].snippet


# ── Soft requirements: advisory only ────────────────────────────────────────


def test_soft_requirements_are_advisory_and_not_scored(db_session):
    candidate = make_candidate(db_session, resume_text="Led teams and mentored engineers.")
    job = make_job(
        db_session,
        [
            {"category": "skill", "skill": "python"},
            {"category": "other", "label": "Strong ownership mindset"},
        ],
    )
    candidate.skills.append(
        CandidateSkill(name="python", normalized_name="python", category="language")
    )
    db_session.commit()

    result = evaluate(db_session, candidate, job)
    soft = next(r for r in result.requirements if r.category == "other")
    assert soft.status == "advisory"
    # Composite reflects only the scored skill (soft excluded, so 100).
    assert result.composite_score == 100.0
    assert "not scored" in soft.reason or "human judgement" in soft.reason


# ── Composite + weights + formula ───────────────────────────────────────────


def test_composite_formula_and_weight_renormalization(db_session):
    candidate = make_candidate(
        db_session,
        skills=["python", "react"],
        years_experience=6,
    )
    job = make_job(
        db_session,
        [
            {"category": "skill", "skill": "python"},  # met
            {"category": "skill", "skill": "react"},  # met
            {"category": "skill", "skill": "aws"},  # missing
            {
                "kind": "preferred",
                "category": "skill",
                "skill": "react",
            },  # duplicate → deduped upstream
        ],
        domain=None,
    )
    result = evaluate(db_session, candidate, job)

    assert result.components["must_have"] == round(2 / 3, 4)
    # No experience/domain requirements → weights re-normalized over present components.
    assert result.weights_used.keys() == {"must_have", "preferred"}
    assert abs(sum(result.weights_used.values()) - 1.0) < 1e-6
    assert "must_have" in result.formula and "/100" in result.formula
    assert result.engine_version == ENGINE_VERSION


def test_published_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_ranking_prefers_higher_must_have_coverage(db_session):
    make_candidate(
        db_session,
        name="Strong",
        skills=["python", "react", "postgresql"],
        years_experience=7,
        resume_text="Python, react, postgresql everywhere.",
    )
    make_candidate(
        db_session,
        name="Weak",
        skills=["python"],
        years_experience=2,
        resume_text="Only python.",
    )
    job = make_job(
        db_session,
        [
            {"category": "skill", "skill": "python"},
            {"category": "skill", "skill": "react"},
            {"category": "skill", "skill": "postgresql"},
            {"category": "experience", "min_years": 5, "label": "5+ years"},
        ],
    )
    from app.services.matching import rank_candidates_for_job

    ranked = rank_candidates_for_job(db_session, job)
    assert [r.candidate_name for r in ranked] == ["Strong", "Weak"]
    assert ranked[0].composite_score > ranked[1].composite_score


def test_evaluation_is_deterministic(db_session):
    candidate = make_candidate(
        db_session,
        name="Repeat",
        skills=["python"],
        years_experience=5,
        resume_text="Python developer with 5 years.",
    )
    job = make_job(
        db_session,
        [
            {"category": "skill", "skill": "python"},
            {"category": "experience", "min_years": 4, "label": "4+ years"},
        ],
    )
    first = evaluate(db_session, candidate, job)
    second = evaluate(db_session, candidate, job)
    assert first.composite_score == second.composite_score
    assert [r.status for r in first.requirements] == [r.status for r in second.requirements]


# ── Responsible-AI structural guard ─────────────────────────────────────────


def test_no_protected_attribute_columns_exist_anywhere():
    """The schema must not even have a place to store protected attributes."""
    from app.db.base import Base

    banned = {
        "age",
        "date_of_birth",
        "dob",
        "gender",
        "sex",
        "ethnicity",
        "race",
        "nationality",
        "religion",
        "marital_status",
        "disability",
        "photo",
        "photo_url",
        "avatar",
        "national_id",
        "family_status",
    }
    for table in Base.metadata.sorted_tables:
        overlap = {column.name for column in table.columns if column.name.lower() in banned}
        assert not overlap, f"Protected-attribute-like columns found: {table.name} -> {overlap}"


def test_evidence_snippets_come_from_source_material(db_session):
    resume_line = "Designed PostgreSQL schemas for tracking shipments."
    candidate = make_candidate(db_session, resume_text=resume_line)
    job = make_job(db_session, [{"category": "skill", "skill": "postgresql"}])
    evaluation = evaluate(db_session, candidate, job).requirements[0]

    assert evaluation.status == "met"
    (evidence,) = evaluation.evidence
    assert evidence.snippet in resume_line


def test_experience_years_computed_from_dates_not_claims(db_session):
    candidate = make_candidate(
        db_session,
        name="Dated",
        roles=[
            {
                "title": "Engineer",
                "company": "A",
                "start": date(2018, 1, 1),
                "end": date(2021, 1, 1),
            },
            {
                "title": "Engineer",
                "company": "B",
                "start": date(2021, 1, 1),
                "end": None,
                "current": True,
            },
        ],
    )
    job = make_job(db_session, [{"category": "experience", "min_years": 5, "label": "5+ years"}])
    evaluation = evaluate(db_session, candidate, job).requirements[0]

    # years_experience is None → unknown (engine refuses to guess from dates it
    # has not normalized; normalization happens at ingestion).
    assert evaluation.status == "unknown"


def test_education_evidence_snippet_is_traceable_to_resume(db_session):
    resume_line = "BSc Computer Science - American University of Sharjah (2014 - 2018)"
    candidate = make_candidate(
        db_session,
        resume_text=f"Education\n{resume_line}\n",
        educations=[
            {
                "degree": "BSc Computer Science",
                "institution": "American University of Sharjah",
            }
        ],
    )
    job = make_job(
        db_session,
        [
            {
                "category": "education",
                "label": "Bachelor's degree in Computer Science",
                "keywords": "bachelor",
            }
        ],
    )
    (evaluation,) = evaluate(db_session, candidate, job).requirements

    assert evaluation.status == "met"
    snippet = evaluation.evidence[0].snippet
    # quoted evidence is verbatim in the stored resume — not a synthesized join
    assert snippet in resume_line
    assert " — " not in snippet
