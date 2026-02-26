from app.scrapers.dedup import find_title_duplicate, title_similarity


def test_title_similarity_high_for_near_duplicates():
    left = "IIT Delhi Summer Research Internship 2026"
    right = "IIT Delhi Summer Research Internship 2026 Program"
    assert title_similarity(left, right) >= 0.9


def test_title_similarity_low_for_unrelated_titles():
    left = "AICTE Scholarship for Data Science Students"
    right = "DRDO Mechanical Engineering Fellowship"
    assert title_similarity(left, right) < 0.9


def test_find_title_duplicate_uses_threshold():
    existing = [
        "IISc Fellowship 2026 in Computer Science",
        "Startup India Entrepreneurship Program",
    ]
    assert (
        find_title_duplicate(
            "IISc Fellowship 2026 in Computer Science Program", existing
        )
        is True
    )
    assert find_title_duplicate("National Law Fellowship 2026", existing) is False
