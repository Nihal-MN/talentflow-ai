"""Embedding providers: OpenAI + a deterministic hashed mock, plus cosine math.

The mock embedder is a hashed bag-of-ngrams random projection: each token
(and token bigram) hashes to one dimension with a ±1 sign, then the vector is
L2-normalized. Cosine similarity between two such vectors approximates lexical
overlap — good enough to make semantic search demonstrable offline, clearly
labeled as ``mock``. Same text → same vector, forever.
"""

from __future__ import annotations

import hashlib
import re
from itertools import pairwise
from typing import Any

import numpy as np

from app.core.config import DEFAULT_EMBEDDING_DIM
from app.core.errors import ProviderUnavailableError

_TOKEN_RE = re.compile(r"[a-z0-9+#.]{2,}")


class HashEmbeddingProvider:
    """Deterministic offline embedder (``mock:hashed-ngram-v1``)."""

    name = "mock"
    model = "hashed-ngram-v1"

    def __init__(self, dim: int = DEFAULT_EMBEDDING_DIM) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = np.zeros(self.dim, dtype=np.float32)
        tokens = _TOKEN_RE.findall(text.lower())
        ngrams: list[tuple[str, float]] = [(token, 1.0) for token in tokens]
        ngrams += [(f"{first}_{second}", 0.5) for first, second in pairwise(tokens)]
        for gram, weight in ngrams:
            digest = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign * weight
        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector /= norm
        return vector.tolist()


class OpenAIEmbeddingProvider:
    """Embeddings from the OpenAI API (default model: text-embedding-3-small)."""

    name = "openai"

    def __init__(
        self,
        *,
        api_key: str = "",
        model: str,
        dim: int = DEFAULT_EMBEDDING_DIM,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.dim = dim
        if client is not None:
            self._client = client  # injected (tests)
            return
        if not api_key:
            raise ProviderUnavailableError("OPENAI_API_KEY is not set")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency is pinned
            raise ProviderUnavailableError("The 'openai' package is not installed") from exc
        self._client = OpenAI(api_key=api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self._client.embeddings.create(model=self.model, input=texts)
        except Exception as exc:
            raise ProviderUnavailableError(f"OpenAI embeddings request failed: {exc}") from exc
        return [[float(value) for value in item.embedding] for item in response.data]


def cosine_similarity(
    vector_a: list[float] | np.ndarray, vector_b: list[float] | np.ndarray
) -> float:
    """Cosine similarity in [-1, 1]; 0.0 for empty/mismatched vectors."""
    array_a = np.asarray(vector_a, dtype=np.float32)
    array_b = np.asarray(vector_b, dtype=np.float32)
    if array_a.shape != array_b.shape or array_a.size == 0:
        return 0.0
    norm_a = float(np.linalg.norm(array_a))
    norm_b = float(np.linalg.norm(array_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(array_a, array_b) / (norm_a * norm_b))
