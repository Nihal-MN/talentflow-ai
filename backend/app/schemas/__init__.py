"""API request/response schemas (Pydantic)."""

from app.schemas.application import (
    ApplicationCreate,
    ApplicationOut,
    StageEventOut,
    StageMove,
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
from app.schemas.common import (
    AIHealth,
    CountsOut,
    DatabaseHealth,
    ErrorBody,
    ErrorResponse,
    HealthOut,
)
from app.schemas.job import (
    JobApplicationBriefOut,
    JobBrief,
    JobCreate,
    JobListItem,
    JobOut,
    JobUpdate,
    RequirementOut,
)
from app.schemas.matching import (
    EvidenceOut,
    MatchResultOut,
    RequirementEvaluationOut,
)
from app.schemas.misc import (
    NoteCreate,
    NoteOut,
    ScreeningListItem,
    ScreeningQuestionOut,
    ScreeningRequest,
    TagCreate,
    TagOut,
)

__all__ = [
    "AIHealth",
    "ApplicationBriefOut",
    "ApplicationCreate",
    "ApplicationOut",
    "CandidateBrief",
    "CandidateListItem",
    "CandidateOut",
    "CertificationOut",
    "CountsOut",
    "DatabaseHealth",
    "EducationOut",
    "ErrorBody",
    "ErrorResponse",
    "EvidenceOut",
    "ExperienceOut",
    "HealthOut",
    "JobApplicationBriefOut",
    "JobBrief",
    "JobCreate",
    "JobListItem",
    "JobOut",
    "JobUpdate",
    "MatchResultOut",
    "NoteCreate",
    "NoteOut",
    "RequirementEvaluationOut",
    "RequirementOut",
    "ScreeningListItem",
    "ScreeningQuestionOut",
    "ScreeningRequest",
    "SkillOut",
    "StageEventOut",
    "StageMove",
    "TagCreate",
    "TagOut",
]
