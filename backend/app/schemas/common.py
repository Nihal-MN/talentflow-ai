"""Shared API schemas: errors, health, counts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    detail: Any | None = None


class ErrorResponse(BaseModel):
    """The single error shape used by every endpoint."""

    error: ErrorBody


class CountsOut(BaseModel):
    candidates: int
    jobs: int
    open_jobs: int
    applications: int


class DatabaseHealth(BaseModel):
    status: Literal["ok", "error"]
    dialect: str
    latency_ms: float | None = None
    detail: str | None = None


class AIHealth(BaseModel):
    """Non-secret AI configuration state (never includes key material)."""

    mode: Literal["auto", "openai", "mock"]
    provider: str
    model: str
    embedding_model: str
    api_key_configured: bool
    misconfigured: bool = False


class HealthOut(BaseModel):
    status: Literal["ok", "degraded"]
    app: str
    version: str
    time: str
    database: DatabaseHealth
    ai: AIHealth
    counts: CountsOut
