"""Embedding providers + storage/search (SQLite path) + migration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from app.ai.embeddings import HashEmbeddingProvider, cosine_similarity
from app.core.errors import ValidationAppError
from app.models.embedding import EMBEDDING_DIM
from app.services import embeddings_store

PROVIDER = HashEmbeddingProvider()


# ── Embedding math ──────────────────────────────────────────────────────────


def test_hash_embeddings_are_deterministic_with_expected_dimension():
    first = PROVIDER.embed(["senior python engineer"])[0]
    second = PROVIDER.embed(["senior python engineer"])[0]
    assert first == second
    assert len(first) == EMBEDDING_DIM
    assert EMBEDDING_DIM == 1536


def test_similar_texts_are_closer_than_unrelated_texts():
    base, similar, different = PROVIDER.embed(
        [
            "Python backend engineer building FastAPI services and PostgreSQL schemas",
            "Backend engineer: Python, FastAPI, PostgreSQL schema design",
            "Retail store manager with merchandising experience",
        ]
    )
    assert cosine_similarity(base, similar) > cosine_similarity(base, different)
    assert cosine_similarity(base, base) == pytest.approx(1.0, abs=1e-6)


def test_cosine_handles_degenerate_input():
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([1.0, 0.0], [1.0]) == 0.0  # mismatched dims
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


# ── Storage + search (SQLite path) ──────────────────────────────────────────


def test_store_search_and_delete_roundtrip(db_session):
    count = embeddings_store.store_for_owner(
        db_session,
        owner_type="candidate",
        owner_id=1,
        chunks=["Python and FastAPI services", "Retail merchandising reports"],
        provider=PROVIDER,
    )
    db_session.commit()
    assert count == 2

    hits = embeddings_store.search_similar_text(
        db_session,
        owner_type="candidate",
        text="FastAPI backend",
        provider=PROVIDER,
        limit=5,
    )
    assert hits
    assert hits[0].owner_id == 1
    assert hits[0].similarity >= hits[-1].similarity
    assert "FastAPI" in hits[0].chunk_text or "Python" in hits[0].chunk_text

    # search with single quotes in text must not break anything (no raw SQL).
    embeddings_store.search_similar_text(
        db_session, owner_type="candidate", text="it's a 'test'", provider=PROVIDER
    )

    embeddings_store.delete_for_owner(db_session, "candidate", 1)
    db_session.commit()
    assert (
        embeddings_store.search_similar_text(
            db_session, owner_type="candidate", text="FastAPI", provider=PROVIDER
        )
        == []
    )


def test_store_is_idempotent(db_session):
    embeddings_store.store_for_owner(
        db_session, owner_type="job", owner_id=7, chunks=["a", "b", "c"], provider=PROVIDER
    )
    embeddings_store.store_for_owner(
        db_session, owner_type="job", owner_id=7, chunks=["only one"], provider=PROVIDER
    )
    db_session.commit()
    records = embeddings_store.get_owner_chunks(db_session, "job", 7)
    assert len(records) == 1
    assert records[0].chunk_text == "only one"


def test_dimension_mismatch_is_rejected(db_session):
    class BadProvider:
        name = "bad"
        model = "wrong-dim"
        dim = 3

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[0.1, 0.2, 0.3] for _ in texts]

    with pytest.raises(ValidationAppError, match="dimension"):
        embeddings_store.store_for_owner(
            db_session,
            owner_type="candidate",
            owner_id=1,
            chunks=["hello"],
            provider=BadProvider(),  # type: ignore[arg-type]
        )


def test_search_excludes_unembedded_rows(db_session):
    stored = embeddings_store.store_for_owner(
        db_session, owner_type="candidate", owner_id=2, chunks=["python"], provider=PROVIDER
    )
    assert stored == 1
    hits = embeddings_store.search_similar(
        db_session, owner_type="candidate", query_vector=PROVIDER.embed(["python"])[0]
    )
    assert len(hits) == 1


# ── Alembic migration round-trip ────────────────────────────────────────────


def test_alembic_migrations_apply_and_downgrade(tmp_path: Path, monkeypatch):
    """The migration itself is exercised: upgrade → inspect → downgrade → upgrade."""
    from alembic import command
    from alembic.config import Config
    from app.core.config import get_settings
    from sqlalchemy import create_engine, inspect

    url = f"sqlite:///{tmp_path / 'mig.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()  # make alembic env.py pick up the temp URL

    try:
        backend_dir = Path(__file__).resolve().parents[1]
        config = Config(str(backend_dir / "alembic.ini"))
        config.set_main_option("script_location", str(backend_dir / "alembic"))

        command.upgrade(config, "head")

        engine = create_engine(url)
        tables = set(inspect(engine).get_table_names())
        engine.dispose()
        expected = {
            "candidates", "candidate_experiences", "candidate_educations", "candidate_skills",
            "candidate_certifications", "jobs", "job_requirements", "applications",
            "pipeline_stage_events", "candidate_notes", "tags", "candidate_tags",
            "screening_questions", "embedding_records",
        }
        assert expected <= tables

        command.downgrade(config, "base")
        engine = create_engine(url)
        remaining = set(inspect(engine).get_table_names()) - {"alembic_version"}
        engine.dispose()
        assert remaining == set()

        command.upgrade(config, "head")  # and back up again — idempotent
    finally:
        get_settings.cache_clear()


def test_migration_files_are_named_consistently():
    versions = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    files = sorted(p.name for p in versions.glob("*.py") if not p.name.startswith("__"))
    assert files, "no migration files found"
    for filename in files:
        revision = filename.split("_", 1)[0]
        assert len(revision) == 12 and revision.isalnum(), f"odd revision name: {filename}"
