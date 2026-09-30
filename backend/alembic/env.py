"""Alembic environment — the database URL and metadata come from the app.

Works for both runtime dialects: PostgreSQL+pgvector (Docker) and the SQLite
dev fallback. ``render_as_batch`` is enabled on SQLite so future migrations
can alter columns there too.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401  (imports every model onto Base.metadata)
from app.core.config import get_settings
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# The HNSW index on ``embedding_records.embedding`` is created via raw DDL in
# the initial migration (pgvector-specific opclass — not portable to SQLite).
# It is intentionally absent from the SQLAlchemy metadata, so autogenerate
# would otherwise propose dropping it on PostgreSQL. Exclude it from
# autogenerate comparison so ``alembic check`` stays clean.
_HNSW_INDEX = "ix_embedding_records_embedding_hnsw"


def _include_object(obj, name, type_, reflected, compare_to):  # noqa: ANN001
    if type_ == "index" and name == _HNSW_INDEX and compare_to is None:
        return False
    return True


def _database_url() -> str:
    return get_settings().sqlalchemy_url


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live connection."""
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=url.startswith("sqlite"),
        include_object=_include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live connection."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        configuration, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=connection.dialect.name == "sqlite",
            include_object=_include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
