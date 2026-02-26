"""Personalization scoring logic for the feed endpoint."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Iterable

from app.ai.embeddings import cosine_similarity


def _to_token_set(values: Iterable[str]) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        cleaned = re.sub(r"[^a-z0-9\s+]", " ", (value or "").lower())
        tokens.update(piece for piece in cleaned.split() if piece)
    return tokens


def interest_match_score(
    profile_embedding: list[float] | None,
    opportunity_embedding: list[float] | None,
    interests: list[str] | None,
    opportunity_text: str,
) -> float:
    if profile_embedding and opportunity_embedding:
        return max(0.0, cosine_similarity(profile_embedding, opportunity_embedding))

    interest_tokens = _to_token_set(interests or [])
    if not interest_tokens:
        return 0.0
    text_tokens = _to_token_set([opportunity_text])
    if not text_tokens:
        return 0.0

    overlap = len(interest_tokens.intersection(text_tokens))
    return min(1.0, overlap / max(1, len(interest_tokens)))


def skill_similarity_score(skills: list[str] | None, opportunity_text: str) -> float:
    skill_tokens = _to_token_set(skills or [])
    if not skill_tokens:
        return 0.0
    text_tokens = _to_token_set([opportunity_text])
    if not text_tokens:
        return 0.0
    overlap = len(skill_tokens.intersection(text_tokens))
    return min(1.0, overlap / max(1, len(skill_tokens)))


def deadline_urgency_score(
    deadline: datetime | None, now: datetime | None = None
) -> float:
    if deadline is None:
        return 0.0

    current = now or datetime.now(timezone.utc)
    remaining_days = (deadline - current).total_seconds() / 86400.0
    if remaining_days <= 0:
        return 1.0

    # High urgency near deadline, smoothly decays as deadline gets farther.
    return 1.0 / (1.0 + math.exp((remaining_days - 7.0) / 2.0))


def compute_relevance_score(
    *,
    interest_match: float,
    skill_similarity: float,
    engagement: float,
    deadline_urgency: float,
) -> float:
    score = (
        max(0.0, min(1.0, interest_match)) * 0.4
        + max(0.0, min(1.0, skill_similarity)) * 0.3
        + max(0.0, min(1.0, engagement)) * 0.2
        + max(0.0, min(1.0, deadline_urgency)) * 0.1
    )
    return round(score, 6)
