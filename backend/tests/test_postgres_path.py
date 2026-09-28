"""PostgreSQL + pgvector path.

Two layers:

* dialect-level checks that ALWAYS run — they compile the real ``<=>`` SQL and
  exercise the embedding type's text serialization for PostgreSQL, so the
  pgvector query construction is verified even without a server;
* one integration test that runs only when ``DATABASE_URL`` points at a
  PostgreSQL instance (CI provides a pgvector service container): it applies
  migrations, stores real vectors and asserts ranked similarity search works.
"""

from __future__ import annotations

import os

import pytest
from app.ai.embeddings import HashEmbeddingProvider
from app.models.embedding import EMBEDDING_DIM, EmbeddingRecord, EmbeddingVector, vector_to_literal
from pgvector.sqlalchemy import Vector
from sqlalchemy import bindparam, cast, select
from sqlalchemy.dialects import postgresql

PG_URL = os.environ.get("DATABASE_URL", "")
needs_postgres = pytest.mark.skipif(
    not PG_URL.startswith("postgresql"),
    reason="requires DATABASE_URL pointing at PostgreSQL (provided in CI)",
)


# ── Dialect-level checks (no server needed) ─────────────────────────────────


def test_embedding_type_binds_lists_on_postgres_and_text_on_sqlite():
    from sqlalchemy.dialects import sqlite as sqlite_module

    lite = sqlite_module.dialect()
    pg = postgresql.dialect()
    column_type = EmbeddingVector()

    # PostgreSQL: hand the raw list to the pgvector impl type (it formats the
    # wire representation itself and *rejects* text — verified against a real
    # server in the integration test below).
    bound_pg = column_type.process_bind_param([0.1, 0.2, 0.3], pg)
    assert bound_pg == [0.1, 0.2, 0.3]

    # SQLite: JSON-encoded text round-trips.
    bound_sqlite = column_type.process_bind_param([0.1, 0.2, 0.3], lite)
    assert isinstance(bound_sqlite, str)
    assert column_type.process_result_value(bound_sqlite, lite) == [0.1, 0.2, 0.3]

    # Results parse from text, lists and ndarrays alike.
    assert column_type.process_result_value("[0.1,0.2,0.3]", pg) == [0.1, 0.2, 0.3]
    assert column_type.process_result_value([0.4, 0.5], pg) == [0.4, 0.5]

    ddl_type = column_type.load_dialect_impl(pg)
    assert "VECTOR" in ddl_type.get_col_spec().upper()


def test_similarity_search_compiles_to_pgvector_operator_sql():
    """The exact SQL the pgvector branch runs: embedding <=> CAST(:vec AS vector)."""
    vector_param = bindparam("query_vector", value=vector_to_literal([0.1] * EMBEDDING_DIM))
    distance = EmbeddingRecord.embedding.op("<=>")(cast(vector_param, Vector(EMBEDDING_DIM)))
    statement = (
        select(EmbeddingRecord, distance.label("distance"))
        .where(EmbeddingRecord.owner_type == "candidate")
        .order_by(distance)
        .limit(5)
    )
    compiled = str(statement.compile(dialect=postgresql.dialect()))
    assert "<=>" in compiled
    assert "CAST(" in compiled
    assert "VECTOR(1536)" in compiled.upper()
    assert "ORDER BY" in compiled.upper()


# ── Integration test (PostgreSQL required) ──────────────────────────────────


@needs_postgres
def test_pgvector_roundtrip_and_ranked_search():
    from alembic import command
    from alembic.config import Config
    from app.core.config import get_settings
    from app.services import embeddings_store
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    get_settings.cache_clear()  # let alembic/env.py see this DATABASE_URL
    try:
        backend_dir = "."
        config = Config(os.path.join(backend_dir, "alembic.ini"))
        config.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
        command.upgrade(config, "head")  # includes CREATE EXTENSION vector + HNSW
    finally:
        get_settings.cache_clear()

    engine = create_engine(PG_URL, pool_pre_ping=True)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    provider = HashEmbeddingProvider()
    owner_id = 9_000_001  # reserved for this test

    try:
        embeddings_store.delete_for_owner(session, "candidate", owner_id)
        session.commit()

        stored = embeddings_store.store_for_owner(
            session,
            owner_type="candidate",
            owner_id=owner_id,
            chunks=[
                "Senior Python engineer building FastAPI services and PostgreSQL schemas",
                "Store manager handling merchandising and retail floor operations",
            ],
            provider=provider,
        )
        session.commit()
        assert stored == 2

        hits = embeddings_store.search_similar_text(
            session,
            owner_type="candidate",
            text="FastAPI backend engineering in Python",
            provider=provider,
            limit=10,
        )
        ours = [hit for hit in hits if hit.owner_id == owner_id]
        assert ours, "stored vectors must be searchable via the <=> operator"
        assert "Python" in ours[0].chunk_text
        assert 0.0 <= ours[0].similarity <= 1.0 + 1e-6

        # Reading the vector back off PostgreSQL round-trips to floats.
        (record,) = embeddings_store.get_owner_chunks(session, "candidate", owner_id)[:1]
        assert record.embedding is not None
        assert len(record.embedding) == EMBEDDING_DIM

        embeddings_store.delete_for_owner(session, "candidate", owner_id)
        session.commit()
    finally:
        session.close()
        engine.dispose()
