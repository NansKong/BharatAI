"""
InCoScore computation engine.
Pure functions — no DB access, fully unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.application import Achievement

# ---------------------------------------------------------------------------
# Score point table (per task specification)
# ---------------------------------------------------------------------------

_HACKATHON_POINTS = {"1st": 100, "2nd": 70, "3rd": 50, "participant": 10}
_COMPETITION_POINTS = {"national": 90, "state": 50, "college": 20}

# Certification sub-types (stored in achievement.description as JSON or plain text)
_CERTIFICATION_INDUSTRY_KEYWORDS = {
    "aws",
    "gcp",
    "azure",
    "ml",
    "tensorflow",
    "pytorch",
    "databricks",
}

BADGE_MILESTONES = [
    (100, "Rising Star"),
    (300, "Domain Explorer"),
    (500, "Achiever"),
    (750, "Elite Scholar"),
    (1000, "InCo Legend"),
]

# Domain weight multipliers — applied to specific component sub-totals
_DOMAIN_WEIGHTS: dict[str, dict[str, float]] = {
    "ai_ds": {"coding": 1.2, "research_internship": 1.2},
    "cs": {"coding": 1.1},
    "management": {"competition": 1.2, "community": 1.1},
    "finance": {"competition": 1.1},
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ScoreComponents:
    hackathon: float = 0.0
    research_internship: float = 0.0
    publication: float = 0.0
    competition: float = 0.0
    certification: float = 0.0
    coding: float = 0.0
    community: float = 0.0

    @property
    def total(self) -> float:
        raw = (
            self.hackathon
            + self.research_internship
            + self.publication
            + self.competition
            + self.certification
            + self.coding
            + self.community
        )
        return min(round(raw, 2), 1000.0)

    def to_dict(self) -> dict:
        return {
            "hackathon": self.hackathon,
            "research_internship": self.research_internship,
            "publication": self.publication,
            "competition": self.competition,
            "certification": self.certification,
            "coding": self.coding,
            "community": self.community,
            "total": self.total,
        }


# ---------------------------------------------------------------------------
# Scoring logic
# ---------------------------------------------------------------------------


def _score_hackathon(description: str | None) -> float:
    desc = (description or "").lower()
    for placement, pts in _HACKATHON_POINTS.items():
        if placement in desc:
            return float(pts)
    return float(_HACKATHON_POINTS["participant"])


def _score_competition(description: str | None) -> float:
    desc = (description or "").lower()
    for level, pts in _COMPETITION_POINTS.items():
        if level in desc:
            return float(pts)
    return float(_COMPETITION_POINTS["college"])


def _score_certification(description: str | None) -> float:
    desc = (description or "").lower()
    if any(kw in desc for kw in _CERTIFICATION_INDUSTRY_KEYWORDS):
        return 60.0
    return 30.0  # NPTEL / other


def _score_publication(description: str | None) -> float:
    desc = (description or "").lower()
    if (
        "peer-reviewed" in desc
        or "ieee" in desc
        or "acm" in desc
        or "springer" in desc
        or "elsevier" in desc
    ):
        return 120.0
    return 40.0  # preprint / unpublished


def compute_incoscore(
    achievements: "list[Achievement]",
    domain: str = "unclassified",
    community_post_count: int = 0,
) -> ScoreComponents:
    """
    Compute InCoScore from a list of VERIFIED achievements.
    Unverified achievements contribute 0 points.
    """
    sc = ScoreComponents()

    research_count = 0

    for ach in achievements:
        if not ach.verified:
            continue  # Only verified achievements count

        t = (ach.type or "").lower()

        if t == "hackathon":
            sc.hackathon += _score_hackathon(ach.description)

        elif t == "internship":
            if research_count < 3:
                sc.research_internship += 80.0
                research_count += 1

        elif t == "publication":
            sc.publication += _score_publication(ach.description)

        elif t == "competition":
            sc.competition += _score_competition(ach.description)

        elif t == "certification":
            sc.certification += _score_certification(ach.description)

        elif t == "coding":
            # points stored in achievement.points_claimed (0–100)
            pts = ach.points_claimed or 0
            sc.coding += float(max(0, min(100, pts)))

    # Community: 0.5 pts per post, capped at 50
    sc.community = min(community_post_count * 0.5, 50.0)

    # Apply domain weight multipliers
    weights = _DOMAIN_WEIGHTS.get(domain, {})
    for component, multiplier in weights.items():
        current = getattr(sc, component, 0.0)
        setattr(sc, component, round(current * multiplier, 2))

    return sc


def assign_badges(total_score: float, achievements: "list[Achievement]") -> list[str]:
    """Return list of badge names earned based on score milestones."""
    badges: list[str] = []
    for threshold, badge in BADGE_MILESTONES:
        if total_score >= threshold:
            badges.append(badge)

    # Special achievement badges
    types = {(ach.type or "").lower() for ach in achievements if ach.verified}
    if "hackathon" in types:
        badges.append("First Hackathon")
    if "publication" in types:
        badges.append("Published Researcher")

    return list(dict.fromkeys(badges))  # deduplicate, preserve order
