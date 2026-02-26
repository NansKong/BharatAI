"""Domain classifier for BharatAI opportunities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

DOMAINS = [
    "AI/DS",
    "Computer Science",
    "Electronics and Communication",
    "Mechanical Engineering",
    "Civil Engineering",
    "Biotechnology",
    "Law",
    "Management",
    "Finance",
    "Humanities",
    "Government and Policy",
]

_LABEL_TO_KEY: dict[str, str] = {
    "AI/DS": "ai_ds",
    "Computer Science": "cs",
    "Electronics and Communication": "ece",
    "Mechanical Engineering": "me",
    "Civil Engineering": "civil",
    "Biotechnology": "biotech",
    "Law": "law",
    "Management": "management",
    "Finance": "finance",
    "Humanities": "humanities",
    "Government and Policy": "govt_policy",
}


@dataclass
class ClassificationResult:
    primary_domain: str
    secondary_domain: Optional[str]
    confidence: float


class DomainClassifier:
    """Zero-shot domain classifier backed by a HuggingFace pipeline.

    The pipeline is intentionally lazy-loaded so unit tests can swap it out
    by assigning to ``classifier._pipeline`` after construction.
    """

    def __init__(self, threshold: float = 0.6) -> None:
        self.threshold = threshold
        self._pipeline = None  # lazy-loaded; tests may inject a mock

    def _get_pipeline(self):
        if self._pipeline is None:  # pragma: no cover
            from transformers import pipeline

            self._pipeline = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
            )
        return self._pipeline

    def classify(self, text: str) -> ClassificationResult:
        pipe = self._get_pipeline()
        result = pipe(text, candidate_labels=DOMAINS, multi_label=True)

        labels: list[str] = result["labels"]
        scores: list[float] = result["scores"]

        top_label = labels[0] if labels else None
        top_score = scores[0] if scores else 0.0

        if top_score < self.threshold or top_label is None:
            return ClassificationResult(
                primary_domain="unclassified",
                secondary_domain=None,
                confidence=top_score,
            )

        primary = _LABEL_TO_KEY.get(
            top_label, re.sub(r"[^a-z0-9]", "_", top_label.lower())
        )

        secondary: Optional[str] = None
        if len(labels) > 1:
            second_label = labels[1]
            second_score = scores[1]
            if (
                second_score >= self.threshold * 0.5
            ):  # secondary threshold is half of primary
                secondary = _LABEL_TO_KEY.get(
                    second_label,
                    re.sub(r"[^a-z0-9]", "_", second_label.lower()),
                )

        return ClassificationResult(
            primary_domain=primary,
            secondary_domain=secondary,
            confidence=top_score,
        )


# Module-level singleton (lazy — pipeline loads on first call)
_classifier: Optional[DomainClassifier] = None


def get_classifier() -> DomainClassifier:
    global _classifier
    if _classifier is None:
        _classifier = DomainClassifier()
    return _classifier


# Alias used by ai_tasks.py and scrape_tasks.py
get_domain_classifier = get_classifier


def classify_text(text: str) -> tuple[str, float]:
    """Legacy helper kept for backward compatibility."""
    result = get_classifier().classify(text)
    return result.primary_domain, result.confidence
