"""Shared FastAPI dependencies (db session, AI providers, settings)."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.ai.base import EmbeddingProvider, LLMProvider
from app.ai.factory import build_embedding_provider, build_llm_provider
from app.core.config import Settings, get_settings
from app.db.session import get_db as _get_db

DbSession = Annotated[Session, Depends(_get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache
def get_llm_provider() -> LLMProvider:
    """The configured LLM provider (cached per process)."""
    return build_llm_provider()


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    """The configured embedding provider (cached per process)."""
    return build_embedding_provider()


LLMDep = Annotated[LLMProvider, Depends(get_llm_provider)]
EmbeddingsDep = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]
