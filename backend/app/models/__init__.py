"""ORM models.

Importing this package registers every table on ``Base.metadata`` (used by
Alembic and by the test fixtures). Domain mapping in docs/ARCHITECTURE.md.
"""

from app.models.application import Application, PipelineStage, PipelineStageEvent
from app.models.candidate import (
    Candidate,
    CandidateCertification,
    CandidateEducation,
    CandidateExperience,
    CandidateSkill,
)
from app.models.embedding import EmbeddingRecord, EmbeddingVector
from app.models.job import Job, JobRequirement
from app.models.note import CandidateNote
from app.models.screening import ScreeningQuestion
from app.models.tag import Tag, candidate_tags

__all__ = [
    "Application",
    "Candidate",
    "CandidateCertification",
    "CandidateEducation",
    "CandidateExperience",
    "CandidateNote",
    "CandidateSkill",
    "EmbeddingRecord",
    "EmbeddingVector",
    "Job",
    "JobRequirement",
    "PipelineStage",
    "PipelineStageEvent",
    "ScreeningQuestion",
    "Tag",
    "candidate_tags",
]
