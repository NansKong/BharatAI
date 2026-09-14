"""Regression tests for the production live-ingestion task.

Covers two failure modes that destroyed data in production:
  * expired opportunities were hard-deleted, cascading into ``applications``
  * the Redis cache was flushed with the pattern ``*``, which also wiped the
    refresh-token whitelist and the revoked-access-token blocklist
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.models.application import Application
from app.models.opportunity import Opportunity
from app.models.user import User
from app.workers import scrape_tasks


class _EmptyScraper:
    """Stands in for the live HTTP scrapers; yields nothing."""

    def __init__(self, *args, **kwargs):
        pass

    async def fetch_real_opportunities(self):
        return []


@pytest.fixture
def stub_ingestion_io(monkeypatch):
    """Neutralise network + Redis I/O, and record the cache patterns purged."""
    import app.core.redis as core_redis
    import app.scrapers.devfolio_api as devfolio_api
    import app.scrapers.rss_scraper as rss_scraper
    import app.scrapers.unstop_api as unstop_api

    monkeypatch.setattr(unstop_api, "UnstopAPIScraper", _EmptyScraper)
    monkeypatch.setattr(devfolio_api, "DevfolioAPIScraper", _EmptyScraper)
    monkeypatch.setattr(rss_scraper, "RSSScraper", _EmptyScraper)

    purged: list[str] = []

    async def fake_init_redis():
        return None

    async def fake_close_redis():
        return None

    async def fake_cache_delete_pattern(pattern: str):
        purged.append(pattern)

    monkeypatch.setattr(core_redis, "init_redis", fake_init_redis)
    monkeypatch.setattr(core_redis, "close_redis", fake_close_redis)
    monkeypatch.setattr(core_redis, "cache_delete_pattern", fake_cache_delete_pattern)
    return purged


def _seed_expired_opportunity_with_application(
    run_async,
) -> tuple[uuid.UUID, uuid.UUID]:
    user_id = uuid.uuid4()
    opportunity_id = uuid.uuid4()

    async def _insert() -> None:
        async with AsyncSessionLocal() as db:
            db.add(
                User(
                    id=user_id,
                    name="Applicant",
                    email=f"applicant-{uuid.uuid4().hex[:8]}@example.com",
                    hashed_password="x",
                    role="student",
                )
            )
            db.add(
                Opportunity(
                    id=opportunity_id,
                    title="Closed National Hackathon",
                    description="A hackathon whose registration deadline has passed.",
                    institution="IIT Bombay",
                    domain="cs",
                    deadline=datetime.now(timezone.utc) - timedelta(days=2),
                    source_url=f"https://example.com/{uuid.uuid4().hex}",
                    content_hash=uuid.uuid4().hex,
                    is_active=True,
                )
            )
            await db.flush()
            db.add(
                Application(
                    user_id=user_id,
                    opportunity_id=opportunity_id,
                    status="accepted",
                )
            )
            await db.commit()

    run_async(_insert())
    return user_id, opportunity_id


def test_ingestion_deactivates_expired_without_destroying_applications(
    run_async, stub_ingestion_io
):
    _, opportunity_id = _seed_expired_opportunity_with_application(run_async)

    run_async(scrape_tasks._run_live_ingestion())

    async def _check():
        async with AsyncSessionLocal() as db:
            opportunity = (
                await db.execute(
                    select(Opportunity).where(Opportunity.id == opportunity_id)
                )
            ).scalar_one_or_none()
            application_count = (
                await db.execute(select(func.count(Application.id)))
            ).scalar_one()
            return opportunity, application_count

    opportunity, application_count = run_async(_check())

    # The expired opportunity is retired, not erased...
    assert opportunity is not None, "expired opportunity was hard-deleted"
    assert opportunity.is_active is False
    # ...so the student's application history survives.
    assert application_count == 1


def test_ingestion_cache_invalidation_is_scoped_to_read_caches(
    run_async, stub_ingestion_io
):
    run_async(scrape_tasks._run_live_ingestion())

    assert (
        "*" not in stub_ingestion_io
    ), "flushing '*' also deletes refresh_jti:* and blocklist:* keys"
    assert "feed:*" in stub_ingestion_io
    assert all(
        not pattern.startswith(("refresh_jti", "blocklist", "rl:"))
        for pattern in stub_ingestion_io
    )
