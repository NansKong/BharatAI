"""Unit tests for the InCoScore computation engine (pure functions, no DB)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.ai.incoscore import assign_badges, compute_incoscore

# ---------------------------------------------------------------------------
# Minimal Achievement stub so tests don't need DB
# ---------------------------------------------------------------------------


@dataclass
class FakeAchievement:
    type: str
    description: Optional[str] = None
    verified: bool = True
    points_claimed: Optional[int] = None
    title: str = "Test Achievement"
    event_date: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_scoring_formula_hackathon_1st_place():
    achievements = [
        FakeAchievement(
            type="hackathon", description="Won 1st place in national hackathon"
        )
    ]
    sc = compute_incoscore(achievements)
    assert sc.hackathon == 100.0
    assert sc.total == 100.0


def test_scoring_hackathon_participant():
    achievements = [
        FakeAchievement(
            type="hackathon", description="Participant in college hackathon"
        )
    ]
    sc = compute_incoscore(achievements)
    assert sc.hackathon == 10.0


def test_scoring_research_internship_capped_at_3():
    achievements = [FakeAchievement(type="internship")] * 5  # 5 internships
    sc = compute_incoscore(achievements)
    assert sc.research_internship == 240.0  # only 3 × 80


def test_scoring_cap_at_1000():
    achievements = [
        FakeAchievement(type="publication", description="IEEE peer-reviewed journal")
    ] * 20
    sc = compute_incoscore(achievements)
    assert sc.total == 1000.0  # cap enforced


def test_unverified_achievements_score_zero():
    achievements = [
        FakeAchievement(type="hackathon", description="1st place", verified=False),
        FakeAchievement(
            type="publication", description="peer-reviewed", verified=False
        ),
    ]
    sc = compute_incoscore(achievements)
    assert sc.total == 0.0


def test_domain_weight_ai_boosts_research_and_coding():
    base = [FakeAchievement(type="internship")]
    sc_default = compute_incoscore(base, domain="unclassified")
    sc_ai = compute_incoscore(base, domain="ai_ds")
    assert sc_ai.research_internship > sc_default.research_internship


def test_community_posts_contribution():
    sc = compute_incoscore([], community_post_count=200)
    # Capped at 50 pts
    assert sc.community == 50.0
    sc2 = compute_incoscore([], community_post_count=10)
    assert sc2.community == 5.0


def test_badges_assigned_at_milestones():
    achievements = [
        FakeAchievement(type="publication", description="peer-reviewed")
    ] * 5  # 600 pts
    sc = compute_incoscore(achievements)
    badges = assign_badges(sc.total, achievements)
    assert "Achiever" in badges  # milestone at 500


def test_badges_not_assigned_below_threshold():
    achievements = [
        FakeAchievement(type="hackathon", description="participant")
    ]  # 10 pts
    sc = compute_incoscore(achievements)
    badges = assign_badges(sc.total, achievements)
    assert "Achiever" not in badges
    assert "Rising Star" not in badges


def test_hackathon_badge_awarded():
    achievements = [FakeAchievement(type="hackathon", description="1st place")]
    sc = compute_incoscore(achievements)
    badges = assign_badges(sc.total, achievements)
    assert "First Hackathon" in badges
