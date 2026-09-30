"""FastAPI application factory.

Run locally:  ``uvicorn app.main:app --reload``
API docs:     http://localhost:8000/docs
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.middleware import RequestLogMiddleware
from app.api.routes import api_router
from app.core.config import get_settings
from app.core.errors import install_error_handlers
from app.core.logging import configure_logging

API_DESCRIPTION = """
TalentFlow AI — open-source AI-native hiring pipeline and explainable
candidate matching platform.

* Jobs are created from pasted text or uploaded documents and their
  requirements are extracted with structured outputs.
* Resumes (PDF/DOCX/TXT) become validated structured candidate profiles.
* Matching is requirement-by-requirement and explainable: met / partial /
  missing with quoted evidence — never an opaque AI score.
* A human recruiter keeps the decision.
"""


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="TalentFlow AI API",
        version=__version__,
        description=API_DESCRIPTION,
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    app.add_middleware(RequestLogMiddleware)
    # CORS is added last so it wraps every response, including error handlers.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count"],
    )

    install_error_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "app": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health",
        }

    return app


app = create_app()
