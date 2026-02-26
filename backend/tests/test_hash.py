from app.scrapers.dedup import compute_content_hash


def test_content_hash_same_input_is_stable():
    h1 = compute_content_hash(
        title="IIT Bombay Research Fellowship",
        description="Apply for funded summer research positions.",
        source_url="https://example.com/fellowship",
    )
    h2 = compute_content_hash(
        title="IIT Bombay Research Fellowship",
        description="Apply for funded summer research positions.",
        source_url="https://example.com/fellowship",
    )
    assert h1 == h2


def test_content_hash_changes_when_content_changes():
    h1 = compute_content_hash(
        title="Opportunity A",
        description="Description A",
        source_url="https://example.com/a",
    )
    h2 = compute_content_hash(
        title="Opportunity B",
        description="Description A",
        source_url="https://example.com/a",
    )
    assert h1 != h2
