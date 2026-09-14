"""Unit tests for InCoScore user-domain inference.

Domain keys drive the InCoScore weight multipliers, so a mis-resolved domain
silently changes a student's score and leaderboard position. The keyword table
must match whole words: "management" must not resolve via the "me" key, and
"economics" must not resolve via the "cs" key.
"""
import pytest
from app.workers.incoscore_tasks import _resolve_user_domain


class _User:
    def __init__(self, degree=None):
        self.degree = degree


class _Profile:
    def __init__(self, interests=None, skills=None):
        self.interests = interests or []
        self.skills = skills or []


@pytest.mark.parametrize(
    "degree,expected",
    [
        ("B.Tech Computer Science and Engineering", "cs"),
        ("B.Tech Mechanical Engineering", "me"),
        ("M.Tech AI", "ai_ds"),
        ("B.Tech Information Technology", "cs"),
        # Regressions: these used to match on substrings.
        ("MBA in Management", "management"),
        ("Business Management", "management"),
        ("B.A. Economics", "finance"),
        ("B.Sc Physics", "unclassified"),
        ("B.Sc Statistics", "unclassified"),
        ("B.Com Commerce", "unclassified"),
    ],
)
def test_degree_resolves_to_expected_domain(degree, expected):
    assert _resolve_user_domain(_User(degree)) == expected


def test_profile_skills_match_whole_words_only():
    # "Training" contains "ai" and "Retail" contains "ai" — neither is AI/DS.
    profile = _Profile(skills=["Training", "Retail"])
    assert _resolve_user_domain(_User(), profile) == "unclassified"

    profile = _Profile(skills=["Machine Learning"])
    assert _resolve_user_domain(_User(), profile) == "ai_ds"


def test_resolved_domains_are_valid_opportunity_domains():
    from app.api.v1.opportunities import VALID_DOMAINS
    from app.workers.incoscore_tasks import DOMAIN_KEY_MAP

    assert set(DOMAIN_KEY_MAP.values()) <= VALID_DOMAINS
