"""ORM → API schema serializers.

Explicit conversion functions keep the mapping (and any computed fields, like
requirement counts) in one auditable place instead of hiding implicit
behavior in model properties.
"""

from __future__ import annotations

from app.models.application import Application, PipelineStageEvent
from app.models.candidate import Candidate
from app.models.job import Job, JobRequirement
from app.models.note import CandidateNote
from app.models.screening import ScreeningQuestion
from app.models.tag import Tag
from app.schemas.application import (
    ApplicationOut,
    StageEventOut,
)
from app.schemas.candidate import (
    ApplicationBriefOut,
    CandidateBrief,
    CandidateListItem,
    CandidateOut,
    CertificationOut,
    EducationOut,
    ExperienceOut,
    SkillOut,
)
from app.schemas.job import (
    JobApplicationBriefOut,
    JobBrief,
    JobListItem,
    JobOut,
    RequirementOut,
)
from app.schemas.matching import MatchResultOut
from app.schemas.misc import (
    NoteOut,
    ScreeningListItem,
    ScreeningQuestionOut,
    TagOut,
    TagUsageOut,
)
from app.services.matching import MatchResult


def candidate_brief(candidate: Candidate) -> CandidateBrief:
    return CandidateBrief(
        id=candidate.id,
        full_name=candidate.full_name,
        headline=candidate.headline,
        location=candidate.location,
        years_experience=candidate.years_experience,
    )


def application_brief(application: Application) -> ApplicationBriefOut:
    return ApplicationBriefOut(
        id=application.id,
        job_id=application.job_id,
        job_title=application.job.title if application.job else "",
        stage=application.stage,
        updated_at=application.updated_at,
    )


def job_brief(job: Job) -> JobBrief:
    return JobBrief(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        status=job.status,
        seniority=job.seniority,
        employment_type=job.employment_type,
        domain=job.domain,
    )


def requirement_out(requirement: JobRequirement) -> RequirementOut:
    return RequirementOut(
        id=requirement.id,
        kind=requirement.kind,
        category=requirement.category,
        label=requirement.label,
        normalized_skill=requirement.normalized_skill,
        min_years=requirement.min_years,
        keywords=[part.strip() for part in (requirement.keywords or "").split(",") if part.strip()],
        order_index=requirement.order_index,
    )


def job_application_brief(application: Application) -> JobApplicationBriefOut:
    return JobApplicationBriefOut(
        id=application.id,
        candidate_id=application.candidate_id,
        candidate_name=application.candidate.full_name if application.candidate else "",
        candidate_headline=application.candidate.headline if application.candidate else None,
        stage=application.stage,
        updated_at=application.updated_at,
    )


def stage_event_out(event: PipelineStageEvent) -> StageEventOut:
    return StageEventOut(
        id=event.id,
        from_stage=event.from_stage,
        to_stage=event.to_stage,
        note=event.note,
        created_at=event.created_at,
    )


def application_out(application: Application, *, include_events: bool = False) -> ApplicationOut:
    return ApplicationOut(
        id=application.id,
        candidate_id=application.candidate_id,
        job_id=application.job_id,
        stage=application.stage,
        created_at=application.created_at,
        updated_at=application.updated_at,
        candidate=candidate_brief(application.candidate),
        job=job_brief(application.job),
        screening_questions_count=len(application.screening_questions)
        if application.screening_questions is not None
        else 0,
        stage_events=[stage_event_out(event) for event in application.stage_events]
        if include_events
        else [],
    )


def _job_counts(job: Job) -> tuple[int, int]:
    must = sum(1 for requirement in job.requirements if requirement.kind == "must_have")
    preferred = sum(1 for requirement in job.requirements if requirement.kind == "preferred")
    return must, preferred


def job_list_item(job: Job) -> JobListItem:
    must, preferred = _job_counts(job)
    return JobListItem(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        status=job.status,
        seniority=job.seniority,
        employment_type=job.employment_type,
        domain=job.domain,
        extraction_method=job.extraction_method,
        created_at=job.created_at,
        must_have_count=must,
        preferred_count=preferred,
        applications_count=len(job.applications) if job.applications is not None else 0,
    )


def job_out(job: Job) -> JobOut:
    must, preferred = _job_counts(job)
    return JobOut(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        status=job.status,
        seniority=job.seniority,
        employment_type=job.employment_type,
        domain=job.domain,
        extraction_method=job.extraction_method,
        created_at=job.created_at,
        must_have_count=must,
        preferred_count=preferred,
        applications_count=len(job.applications) if job.applications is not None else 0,
        source=job.source,
        extraction_model=job.extraction_model,
        description_text=job.description_text,
        requirements=[requirement_out(requirement) for requirement in job.requirements],
        applications=[
            job_application_brief(application) for application in (job.applications or [])
        ],
    )


def candidate_list_item(candidate: Candidate) -> CandidateListItem:
    return CandidateListItem(
        id=candidate.id,
        full_name=candidate.full_name,
        headline=candidate.headline,
        location=candidate.location,
        years_experience=candidate.years_experience,
        extraction_method=candidate.extraction_method,
        created_at=candidate.created_at,
        skills=[skill.normalized_name for skill in candidate.skills],
        applications_count=len(candidate.applications) if candidate.applications is not None else 0,
    )


def candidate_out(candidate: Candidate) -> CandidateOut:
    return CandidateOut(
        id=candidate.id,
        full_name=candidate.full_name,
        email=candidate.email,
        phone=candidate.phone,
        location=candidate.location,
        headline=candidate.headline,
        summary=candidate.summary,
        years_experience=candidate.years_experience,
        linkedin_url=candidate.linkedin_url,
        github_url=candidate.github_url,
        website_url=candidate.website_url,
        resume_filename=candidate.resume_filename,
        resume_text=candidate.resume_text,
        extraction_method=candidate.extraction_method,
        extraction_model=candidate.extraction_model,
        created_at=candidate.created_at,
        experiences=[ExperienceOut.model_validate(item) for item in candidate.experiences],
        educations=[EducationOut.model_validate(item) for item in candidate.educations],
        skills=[SkillOut.model_validate(item) for item in candidate.skills],
        certifications=[CertificationOut.model_validate(item) for item in candidate.certifications],
        applications=[application_brief(item) for item in candidate.applications],
        notes=[
            note_out(item)
            for item in sorted(candidate.notes, key=lambda n: n.created_at, reverse=True)
        ],
        tags=[tag_out(item) for item in candidate.tags],
    )


def note_out(note: CandidateNote) -> NoteOut:
    return NoteOut(
        id=note.id,
        candidate_id=note.candidate_id,
        job_id=note.job_id,
        author=note.author,
        body=note.body,
        created_at=note.created_at,
    )


def tag_out(tag: Tag) -> TagOut:
    return TagOut(id=tag.id, name=tag.name, color=tag.color)


def tag_usage_out(tag: Tag, usage_count: int) -> TagUsageOut:
    return TagUsageOut(id=tag.id, name=tag.name, color=tag.color, usage_count=usage_count)


def screening_question_out(question: ScreeningQuestion) -> ScreeningQuestionOut:
    return ScreeningQuestionOut(
        id=question.id,
        application_id=question.application_id,
        category=question.category,
        question=question.question,
        rationale=question.rationale,
        source=question.source,
        order_index=question.order_index,
        created_at=question.created_at,
    )


def screening_list_item(application: Application) -> ScreeningListItem:
    questions = application.screening_questions or []
    newest = max((question.created_at for question in questions), default=None)
    return ScreeningListItem(
        application_id=application.id,
        candidate_id=application.candidate_id,
        candidate_name=application.candidate.full_name if application.candidate else "",
        job_id=application.job_id,
        job_title=application.job.title if application.job else "",
        stage=application.stage,
        source=questions[0].source if questions else "unknown",
        question_count=len(questions),
        created_at=newest,
    )


def match_result_out(result: MatchResult) -> MatchResultOut:
    return MatchResultOut.model_validate(result.as_dict())
