"""Application error taxonomy and structured error responses.

Every error leaving the API shares one JSON shape::

    {"error": {"code": "...", "message": "...", "detail": ...}}

so the frontend can render errors consistently without parsing strings.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Base class for expected application failures."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, detail: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class NotFoundError(AppError):
    """Requested entity does not exist."""

    status_code = 404
    code = "not_found"


class ValidationAppError(AppError):
    """Input passed schema validation but is semantically invalid."""

    status_code = 422
    code = "validation_error"


class IngestionError(AppError):
    """A resume/JD document could not be read or understood."""

    status_code = 422
    code = "ingestion_error"


class ConflictError(AppError):
    """The requested state change conflicts with existing data."""

    status_code = 409
    code = "conflict"


class ProviderUnavailableError(AppError):
    """A required external provider (e.g. OpenAI) is not usable right now."""

    status_code = 503
    code = "provider_unavailable"


def error_payload(code: str, message: str, detail: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": {"code": code, "message": message}}
    if detail is not None:
        payload["error"]["detail"] = detail
    return payload


def install_error_handlers(app: FastAPI) -> None:
    """Register handlers so all failures share one response shape."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.code, exc.message, exc.detail),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
        }.get(exc.status_code, "http_error")
        return JSONResponse(
            status_code=exc.status_code, content=error_payload(code, str(exc.detail))
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [
            {
                "loc": ".".join(str(part) for part in error.get("loc", [])),
                "message": error.get("msg", ""),
                "type": error.get("type", ""),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_payload("validation_error", "Request validation failed", fields),
        )
