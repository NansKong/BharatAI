"""Hash and title-similarity helpers for duplicate detection."""

import math
import re
from collections import Counter
from typing import Iterable

from app.scrapers.base import BaseScraper

TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(value: str) -> list[str]:
    normalized = BaseScraper.sanitize_text(value).lower()
    return TOKEN_RE.findall(normalized)


def compute_content_hash(title: str, description: str, source_url: str) -> str:
    return BaseScraper.build_content_hash(
        title=title, description=description, source_url=source_url
    )


def title_similarity(left: str, right: str) -> float:
    """Cosine similarity over lowercase word-frequency vectors."""
    left_tokens = _tokenize(left)
    right_tokens = _tokenize(right)
    if not left_tokens or not right_tokens:
        return 0.0

    left_vec = Counter(left_tokens)
    right_vec = Counter(right_tokens)

    common = set(left_vec.keys()) & set(right_vec.keys())
    numerator = sum(left_vec[token] * right_vec[token] for token in common)
    left_norm = math.sqrt(sum(v * v for v in left_vec.values()))
    right_norm = math.sqrt(sum(v * v for v in right_vec.values()))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    return numerator / (left_norm * right_norm)


def find_title_duplicate(
    candidate: str, existing_titles: Iterable[str], threshold: float = 0.9
) -> bool:
    for title in existing_titles:
        if title_similarity(candidate, title) >= threshold:
            return True
    return False
