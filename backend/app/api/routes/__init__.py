"""API router aggregation — mounted under the configured API prefix."""

from fastapi import APIRouter

from app.api.routes import applications, candidates, health, jobs, matching, screening, tags

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(jobs.router)
api_router.include_router(candidates.router)
api_router.include_router(applications.router)
api_router.include_router(matching.router)
api_router.include_router(screening.router)
api_router.include_router(tags.router)

__all__ = ["api_router"]
