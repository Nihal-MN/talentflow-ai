"""Application settings.

Everything is environment-driven with safe defaults, so the application runs
with zero configuration: SQLite storage and the deterministic mock AI provider.
Copy `.env.example` to `.env` at the repository root to override anything.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

#: Defaults used when the corresponding env var is unset or blank.
DEFAULT_OPENAI_MODEL = "gpt-5.6-terra"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIM = 1536
DEFAULT_SQLITE_URL = "sqlite:///./data/talentflow.db"


class Settings(BaseSettings):
    """Runtime configuration (env vars > .env files > built-in defaults)."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "TalentFlow AI"
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ── Storage ──────────────────────────────────────────────────────────────
    # Empty → zero-setup SQLite fallback (dev/tests). Docker Compose sets a
    # PostgreSQL+pgvector URL. See docs/adr/0001.
    database_url: str = ""
    upload_dir: str = "./data/uploads"

    # ── AI ───────────────────────────────────────────────────────────────────
    # auto   → OpenAI when OPENAI_API_KEY is set, otherwise the mock provider
    # openai → always use the OpenAI API (fails loudly without a key)
    # mock   → always use the deterministic offline mock
    ai_provider: Literal["auto", "openai", "mock"] = "auto"
    openai_api_key: str = ""
    openai_model: str = ""
    openai_embedding_model: str = ""
    embedding_dim: int = DEFAULT_EMBEDDING_DIM

    @property
    def sqlalchemy_url(self) -> str:
        return self.database_url.strip() or DEFAULT_SQLITE_URL

    @property
    def is_sqlite(self) -> bool:
        return self.sqlalchemy_url.startswith("sqlite")

    @property
    def openai_key_present(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def effective_openai_model(self) -> str:
        return self.openai_model.strip() or DEFAULT_OPENAI_MODEL

    @property
    def effective_openai_embedding_model(self) -> str:
        return self.openai_embedding_model.strip() or DEFAULT_OPENAI_EMBEDDING_MODEL

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton (tests may call ``get_settings.cache_clear()``)."""
    return Settings()
