"""Embedding utilities with graceful fallbacks."""

from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache
from typing import Iterable

from app.core.config import settings

FALLBACK_EMBEDDING_DIM = 384


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


@lru_cache(maxsize=1)
def _load_sentence_transformer():
    try:  # pragma: no cover - model load depends on environment/network cache
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(settings.HUGGINGFACE_MODEL_EMBEDDINGS)
    except Exception:
        return None


def _fallback_embedding(
    text: str, dimension: int = FALLBACK_EMBEDDING_DIM
) -> list[float]:
    """Deterministic hash embedding used when transformer models are unavailable."""
    normalized = text.encode("utf-8")
    if not normalized:
        return [0.0] * dimension

    values: list[float] = []
    for i in range(dimension):
        digest = hashlib.sha256(normalized + i.to_bytes(2, "little")).digest()
        values.append((int.from_bytes(digest[:2], "little") / 65535.0) - 0.5)

    norm = math.sqrt(sum(v * v for v in values))
    if norm == 0:
        return values
    return [v / norm for v in values]


def generate_embedding(text: str) -> list[float]:
    cleaned = _clean_text(text)
    if not cleaned:
        return []

    model = _load_sentence_transformer()
    if model is None:
        return _fallback_embedding(cleaned)

    vector = model.encode(cleaned, normalize_embeddings=True)
    if hasattr(vector, "tolist"):
        return vector.tolist()
    return list(vector)


def cosine_similarity(a: Iterable[float], b: Iterable[float]) -> float:
    vec_a = list(a)
    vec_b = list(b)
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot = sum(x * y for x, y in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(y * y for y in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))


def build_profile_text(
    *, bio: str | None, skills: list[str] | None, interests: list[str] | None
) -> str:
    parts = [
        _clean_text(bio or ""),
        _clean_text(", ".join(skills or [])),
        _clean_text(", ".join(interests or [])),
    ]
    return _clean_text(" ".join(part for part in parts if part))


def build_opportunity_text(
    *, title: str, description: str, domain: str | None, institution: str | None
) -> str:
    parts = [title, description, domain or "", institution or ""]
    return _clean_text(" ".join(parts))
