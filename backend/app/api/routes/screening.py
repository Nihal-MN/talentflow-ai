"""Screening-question endpoints: view stored sets and generate new ones."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession, LLMDep
from app.api.serializers import screening_list_item, screening_question_out
from app.schemas.misc import ScreeningListItem, ScreeningQuestionOut
from app.services import screening as screening_service

router = APIRouter(prefix="/screening", tags=["screening"])


@router.get("", response_model=list[ScreeningListItem], summary="Applications with question sets")
def list_sets(db: DbSession) -> list[ScreeningListItem]:
    applications = screening_service.list_applications_with_questions(db)
    return [screening_list_item(application) for application in applications]


@router.get(
    "/applications/{application_id}",
    response_model=list[ScreeningQuestionOut],
    summary="Stored questions for an application",
)
def list_questions(application_id: int, db: DbSession) -> list[ScreeningQuestionOut]:
    questions = screening_service.list_for_application(db, application_id)
    return [screening_question_out(question) for question in questions]


@router.post(
    "/applications/{application_id}/generate",
    response_model=list[ScreeningQuestionOut],
    status_code=201,
    summary="Generate candidate-specific screening questions",
)
def generate_questions(
    application_id: int, db: DbSession, llm: LLMDep
) -> list[ScreeningQuestionOut]:
    questions = screening_service.generate_for_application(db, application_id, provider=llm)
    return [screening_question_out(question) for question in questions]
