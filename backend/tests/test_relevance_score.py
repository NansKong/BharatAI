from datetime import datetime, timedelta, timezone

from app.ai.personalization import (compute_relevance_score,
                                    deadline_urgency_score)


def test_relevance_score_formula():
    score = compute_relevance_score(
        interest_match=0.75,
        skill_similarity=0.50,
        engagement=0.25,
        deadline_urgency=0.10,
    )
    expected = round((0.75 * 0.4) + (0.50 * 0.3) + (0.25 * 0.2) + (0.10 * 0.1), 6)
    assert score == expected


def test_deadline_urgency_higher_for_near_deadline():
    now = datetime.now(timezone.utc)
    soon = deadline_urgency_score(now + timedelta(days=1), now=now)
    far = deadline_urgency_score(now + timedelta(days=30), now=now)
    assert soon > far
