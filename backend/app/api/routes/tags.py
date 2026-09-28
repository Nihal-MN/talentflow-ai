"""Tag endpoints (candidate tags are managed through /candidates)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.serializers import tag_usage_out
from app.schemas.misc import TagUsageOut
from app.services import candidate_service

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagUsageOut], summary="List tags with usage counts")
def list_tags(db: DbSession) -> list[TagUsageOut]:
    return [tag_usage_out(tag, count) for tag, count in candidate_service.list_tags(db)]
