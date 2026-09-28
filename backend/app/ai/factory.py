"""Provider selection — the one place that decides mock vs OpenAI.

``AI_PROVIDER=auto`` (default): OpenAI when ``OPENAI_API_KEY`` is set,
otherwise the deterministic mock. ``openai`` forces the API; ``mock`` forces
offline. See docs/adr/0002.
"""

from __future__ import annotations

from app.ai.base import EmbeddingProvider, LLMProvider
from app.ai.embeddings import HashEmbeddingProvider, OpenAIEmbeddingProvider
from app.ai.mock_provider import MockLLMProvider
from app.ai.openai_provider import OpenAILLMProvider
from app.core.config import Settings, get_settings


def _use_openai(settings: Settings) -> bool:
    if settings.ai_provider == "openai":
        return True
    if settings.ai_provider == "mock":
        return False
    return settings.openai_key_present  # auto


def build_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """Instantiate the configured LLM provider."""
    settings = settings or get_settings()
    if _use_openai(settings):
        return OpenAILLMProvider(
            api_key=settings.openai_api_key,
            model=settings.effective_openai_model,
            embedding_model=settings.effective_openai_embedding_model,
        )
    return MockLLMProvider()


def build_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    """Instantiate the configured embedding provider."""
    settings = settings or get_settings()
    if _use_openai(settings):
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.effective_openai_embedding_model,
            dim=settings.embedding_dim,
        )
    return HashEmbeddingProvider(dim=settings.embedding_dim)


def provider_status(settings: Settings | None = None) -> dict[str, object]:
    """Non-secret AI configuration summary for the System Health page."""
    settings = settings or get_settings()
    wants_openai = _use_openai(settings)
    misconfigured = settings.ai_provider == "openai" and not settings.openai_key_present
    return {
        "mode": settings.ai_provider,
        "provider": "openai" if wants_openai else "mock",
        "model": settings.effective_openai_model if wants_openai else MockLLMProvider.model,
        "embedding_model": settings.effective_openai_embedding_model
        if wants_openai
        else HashEmbeddingProvider.model,
        "api_key_configured": settings.openai_key_present,
        "misconfigured": misconfigured,
    }
