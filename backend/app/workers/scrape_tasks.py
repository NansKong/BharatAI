"""Scraping Celery tasks with duplicate checks and failure accounting."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from celery.exceptions import MaxRetriesExceededError, Retry
from prometheus_client import Counter
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import AsyncSessionLocal, close_database
from app.models.incoscore import Notification
from app.models.opportunity import MonitoredSource, Opportunity, ScrapeDeadLetter
from app.models.user import User
from app.scrapers import (
    build_source_scraper,
    compute_content_hash,
    find_title_duplicate,
)
from app.scrapers.base import BaseScraper
from app.workers.ai_tasks import classify_opportunity
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

SCRAPE_SUCCESS_TOTAL = Counter(
    "scrape_success_total",
    "Count of successful source scrapes",
    ["source_id"],
)
SCRAPE_FAILURE_TOTAL = Counter(
    "scrape_failure_total",
    "Count of failed source scrapes",
    ["source_id"],
)
OPPORTUNITIES_CREATED_TOTAL = Counter(
    "opportunities_created_total",
    "Count of opportunities created by scrape domain",
    ["domain"],
)


def _backoff_seconds(retries: int) -> int:
    return min(2 ** max(1, retries + 1), 8)


async def _run_with_db_cleanup(coro):
    try:
        return await coro
    finally:
        await close_database()


def _build_scraper(source: MonitoredSource) -> BaseScraper:
    return build_source_scraper(
        source_name=source.name,
        source_url=source.url,
        scrape_type=source.type,
        proxy_list=settings.proxy_list,
    )


async def _get_active_source_ids() -> list[str]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MonitoredSource.id).where(MonitoredSource.active.is_(True))
        )
        return [str(source_id) for source_id in result.scalars().all()]


async def _notify_admins_of_scrape_failure(db, source: MonitoredSource) -> None:
    admin_ids = (
        (
            await db.execute(
                select(User.id).where(User.role == "admin", User.is_active.is_(True))
            )
        )
        .scalars()
        .all()
    )
    if not admin_ids:
        return

    payload = json.dumps(
        {
            "source_id": str(source.id),
            "source_name": source.name,
            "failure_count": source.failure_count,
            "last_error": source.last_error,
        }
    )
    for admin_id in admin_ids:
        db.add(
            Notification(
                user_id=admin_id,
                type="system",
                title="Scraper failure threshold exceeded",
                message=f"Source '{source.name}' has failed {source.failure_count} consecutive times.",
                payload_json=payload,
            )
        )


async def _load_existing_titles(db) -> list[str]:
    rows = await db.execute(
        select(Opportunity.title).where(Opportunity.is_active.is_(True))
    )
    return [title for title in rows.scalars().all() if title]


async def _log_dead_letter(
    *,
    task_name: str,
    source_id: str | None,
    payload: dict,
    error_message: str,
    retry_count: int,
) -> str:
    parsed_source_id = None
    if source_id:
        try:
            parsed_source_id = UUID(source_id)
        except ValueError:
            parsed_source_id = None

    async with AsyncSessionLocal() as db:
        dead_letter = ScrapeDeadLetter(
            task_name=task_name,
            source_id=parsed_source_id,
            payload_json=json.dumps(payload),
            error_message=BaseScraper.sanitize_text(error_message)[:4000],
            retry_count=max(0, retry_count),
        )
        db.add(dead_letter)
        await db.commit()
        return str(dead_letter.id)


async def _scrape_source(source_id: UUID) -> dict:
    async with AsyncSessionLocal() as db:
        source = (
            await db.execute(
                select(MonitoredSource).where(MonitoredSource.id == source_id)
            )
        ).scalar_one_or_none()
        if not source:
            return {"status": "not_found", "source_id": str(source_id)}
        if not source.active:
            return {"status": "inactive", "source_id": str(source_id)}

        scraper = _build_scraper(source)
        now = datetime.now(timezone.utc)

        try:
            scraped_items = await scraper.scrape()
        except Exception as exc:
            source.failure_count += 1
            source.last_error = BaseScraper.sanitize_text(str(exc))[:1000]
            source.last_scraped_at = now
            SCRAPE_FAILURE_TOTAL.labels(source_id=str(source.id)).inc()

            if source.failure_count > 5:
                logger.warning(
                    "Scrape failure threshold exceeded",
                    extra={
                        "source_id": str(source.id),
                        "failure_count": source.failure_count,
                    },
                )
                await _notify_admins_of_scrape_failure(db, source)

            await db.commit()
            return {
                "status": "failure",
                "source_id": str(source.id),
                "failure_count": source.failure_count,
                "error": source.last_error,
            }

        existing_titles = await _load_existing_titles(db)
        created = 0
        created_opportunities: list[Opportunity] = []
        skipped_hash = 0
        skipped_similar = 0

        for item in scraped_items:
            content_hash = compute_content_hash(
                item.title, item.description, item.source_url
            )
            by_hash = (
                await db.execute(
                    select(Opportunity.id).where(
                        Opportunity.content_hash == content_hash
                    )
                )
            ).scalar_one_or_none()
            if by_hash:
                skipped_hash += 1
                continue

            if find_title_duplicate(item.title, existing_titles, threshold=0.9):
                skipped_similar += 1
                continue

            opportunity = Opportunity(
                title=BaseScraper.sanitize_text(item.title)[:500],
                description=BaseScraper.sanitize_text(item.description),
                institution=source.name,
                domain="unclassified",
                deadline=item.deadline,
                source_url=item.source_url,
                application_link=item.application_link,
                eligibility=BaseScraper.sanitize_text(item.eligibility or ""),
                content_hash=content_hash,
                is_active=True,
                is_verified=False,
                source_id=source.id,
            )
            db.add(opportunity)
            existing_titles.append(opportunity.title)
            created += 1
            created_opportunities.append(opportunity)

        source.last_scraped_at = now
        source.failure_count = 0
        source.last_error = None

        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            return {
                "status": "duplicate_conflict",
                "source_id": str(source.id),
            }

        SCRAPE_SUCCESS_TOTAL.labels(source_id=str(source.id)).inc()
        if created > 0:
            OPPORTUNITIES_CREATED_TOTAL.labels(domain="unclassified").inc(created)
            for created_opp in created_opportunities:
                opportunity_id = str(created_opp.id)
                try:
                    classify_opportunity.delay(opportunity_id)
                except Exception:
                    logger.warning(
                        "Failed to queue classification for scraped opportunity",
                        extra={
                            "opportunity_id": opportunity_id,
                            "source_id": str(source.id),
                        },
                    )

        status = "created" if created > 0 else "skipped"
        return {
            "status": status,
            "source_id": str(source.id),
            "created": created,
            "skipped_hash": skipped_hash,
            "skipped_similar": skipped_similar,
        }


@celery_app.task(
    name="app.workers.scrape_tasks.scrape_all_sources", bind=True, max_retries=3
)
def scrape_all_sources(self):
    """Scrape all active monitored sources."""
    logger.info("Starting scheduled scrape of all active sources")

    try:
        source_ids = asyncio.run(_run_with_db_cleanup(_get_active_source_ids()))
    except Exception as exc:
        countdown = _backoff_seconds(self.request.retries)
        logger.exception(
            "Failed to fetch active sources", extra={"countdown": countdown}
        )
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            dead_letter_id = asyncio.run(
                _run_with_db_cleanup(
                    _log_dead_letter(
                        task_name=self.name,
                        source_id=None,
                        payload={"status": "failure", "stage": "load_active_sources"},
                        error_message=str(exc),
                        retry_count=self.request.retries,
                    )
                )
            )
            return {"status": "dead_lettered", "dead_letter_id": dead_letter_id}

    for source_id in source_ids:
        scrape_single_source.delay(source_id)

    logger.info("Queued scrape jobs", extra={"queued": len(source_ids)})
    return {"queued_sources": len(source_ids)}


@celery_app.task(
    name="app.workers.scrape_tasks.scrape_single_source", bind=True, max_retries=3
)
def scrape_single_source(self, source_id: str):
    """Scrape a single monitored source by ID (on-demand)."""
    logger.info("Scraping single source", extra={"source_id": source_id})

    try:
        source_uuid = UUID(source_id)
    except ValueError:
        logger.error("Invalid source_id", extra={"source_id": source_id})
        return {"status": "invalid_source_id", "source_id": source_id}

    try:
        result = asyncio.run(_run_with_db_cleanup(_scrape_source(source_uuid)))
        if result.get("status") == "failure":
            countdown = _backoff_seconds(self.request.retries)
            retry_error = RuntimeError(result.get("error", "scrape failed"))
            logger.warning(
                "Scrape failed; scheduling retry",
                extra={
                    "source_id": source_id,
                    "countdown": countdown,
                    "retries": self.request.retries,
                },
            )
            try:
                raise self.retry(exc=retry_error, countdown=countdown)
            except MaxRetriesExceededError:
                dead_letter_id = asyncio.run(
                    _run_with_db_cleanup(
                        _log_dead_letter(
                            task_name=self.name,
                            source_id=source_id,
                            payload=result,
                            error_message=result.get("error", "scrape failed"),
                            retry_count=self.request.retries,
                        )
                    )
                )
                result["status"] = "dead_lettered"
                result["dead_letter_id"] = dead_letter_id
                logger.error("Scrape moved to dead letter queue", extra=result)
                return result

        logger.info("Scrape single source result", extra=result)
        return result
    except Retry:
        raise
    except Exception as exc:
        countdown = _backoff_seconds(self.request.retries)
        logger.exception(
            "Scrape single source failed",
            extra={"source_id": source_id, "countdown": countdown},
        )
        try:
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            dead_letter_id = asyncio.run(
                _run_with_db_cleanup(
                    _log_dead_letter(
                        task_name=self.name,
                        source_id=source_id,
                        payload={"status": "failure", "source_id": source_id},
                        error_message=str(exc),
                        retry_count=self.request.retries,
                    )
                )
            )
            return {
                "status": "dead_lettered",
                "source_id": source_id,
                "dead_letter_id": dead_letter_id,
            }


# ── URL Health-Check task ─────────────────────────────────────────────────────


async def _run_url_health_check() -> dict:
    """Check all active MonitoredSource URLs and deactivate broken ones."""
    import httpx

    TIMEOUT = 12
    HEADERS = {"User-Agent": "BharatAI URL Checker/1.0"}
    OK_CODES = {200, 201, 202, 203, 206, 301, 302, 303, 307, 308}
    SKIP_CODES = {403, 429}
    SSL_KEYWORDS = ("ssl", "certificate", "dh key", "handshake", "verify")

    def _is_ssl_err(msg: str) -> bool:
        m = msg.lower()
        return any(k in m for k in SSL_KEYWORDS)

    async def _ssl_retry(url: str) -> tuple[bool, int]:
        try:
            async with httpx.AsyncClient(verify=False, timeout=TIMEOUT) as c:
                r = await c.head(url, headers=HEADERS, follow_redirects=True)
                if r.status_code in SKIP_CODES:
                    r = await c.get(url, headers=HEADERS, follow_redirects=True)
                return (
                    r.status_code in OK_CODES or r.status_code in SKIP_CODES
                ), r.status_code
        except Exception:
            return False, 0

    async def _check(client: httpx.AsyncClient, url: str) -> tuple[bool, int, str]:
        try:
            r = await client.head(
                url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True
            )
            if r.status_code in SKIP_CODES:
                r = await client.get(
                    url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True
                )
            return (
                (r.status_code in OK_CODES or r.status_code in SKIP_CODES),
                r.status_code,
                "",
            )
        except httpx.ConnectError as e:
            err = str(e)
            if _is_ssl_err(err):
                ok, code = await _ssl_retry(url)
                if ok:
                    return True, code, "ssl_unverified"
            return False, 0, err[:120]
        except httpx.TimeoutException:
            return False, 0, "timeout"
        except httpx.TooManyRedirects:
            return False, 0, "too_many_redirects"
        except Exception as e:
            err = str(e)
            if _is_ssl_err(err):
                ok, code = await _ssl_retry(url)
                if ok:
                    return True, code, "ssl_unverified"
            return False, 0, err[:120]

    ok_count = broken_count = deactivated_count = 0
    sem = asyncio.Semaphore(20)

    async with AsyncSessionLocal() as db:
        sources = (
            (
                await db.execute(
                    select(MonitoredSource).where(MonitoredSource.active.is_(True))
                )
            )
            .scalars()
            .all()
        )

        async def bounded_check(source):
            async with sem:
                async with httpx.AsyncClient() as client:
                    return source, *(await _check(client, source.url))

        results = await asyncio.gather(*[bounded_check(s) for s in sources])

        for source, ok, code, err in results:
            if ok:
                ok_count += 1
                source.failure_count = 0
                source.last_error = None
            else:
                broken_count += 1
                source.failure_count = (source.failure_count or 0) + 1
                source.last_error = f"URL check: HTTP {code} – {err}"[:500]
                if source.failure_count >= 10:
                    source.active = False
                    deactivated_count += 1

        await db.commit()

    return {"ok": ok_count, "broken": broken_count, "deactivated": deactivated_count}


@celery_app.task(name="app.workers.scrape_tasks.check_url_health", bind=True)
def check_url_health(self):
    """Periodic URL health-check — guarded by a Redis lock to prevent concurrent runs.

    Uses SET NX with a 60-minute TTL so if a manual run and the scheduled
    run fire at the same time, only one proceeds; the other exits cleanly.
    """
    import redis

    LOCK_KEY = "bharatai:url_health_check:lock"
    LOCK_TTL = 60 * 60  # 1 hour in seconds

    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    acquired = r.set(LOCK_KEY, self.request.id or "manual", nx=True, ex=LOCK_TTL)

    if not acquired:
        logger.info("check_url_health: another run is in progress, skipping")
        return {"status": "skipped", "reason": "lock_held"}

    try:
        result = asyncio.run(_run_url_health_check())
        logger.info("URL health check complete", extra=result)
        return result
    finally:
        r.delete(LOCK_KEY)


# ── Production Opportunity Ingestion Task ───────────────────────────────────


async def _run_live_ingestion() -> dict:
    """Production ingestion routine for real-time opportunities across Unstop, Devfolio & RSS."""
    from sqlalchemy import func, update

    from app.core.redis import cache_delete_pattern, close_redis, init_redis
    from app.scrapers.base import BaseScraper
    from app.scrapers.devfolio_api import DevfolioAPIScraper
    from app.scrapers.indian_research_scraper import IndianResearchScraper
    from app.scrapers.internship_api import InternshipAPIScraper
    from app.scrapers.rss_scraper import RSSScraper
    from app.scrapers.unstop_api import UnstopAPIScraper

    real_items = []

    # 1. Unstop API (10 pages per category including internships, hackathons, jobs)
    try:
        u_scraper = UnstopAPIScraper(
            max_pages=10, url="https://unstop.com", scrape_type="dynamic"
        )
        u_items = await u_scraper.fetch_real_opportunities()
        real_items.extend(u_items)
    except Exception as e:
        logger.warning(f"Live ingestion Unstop error: {e}")

    # 2. Devfolio API (10 pages)
    try:
        d_scraper = DevfolioAPIScraper(
            max_pages=10, url="https://devfolio.co", scrape_type="dynamic"
        )
        d_items = await d_scraper.fetch_real_opportunities()
        real_items.extend(d_items)
    except Exception as e:
        logger.warning(f"Live ingestion Devfolio error: {e}")

    # 3. Premier Indian Research Fellowships & IIT Academic Internships
    try:
        res_scraper = IndianResearchScraper(
            url="https://ird.iitd.ac.in", scrape_type="dynamic"
        )
        res_items = await res_scraper.fetch_real_opportunities()
        real_items.extend(res_items)
    except Exception as e:
        logger.warning(f"Live ingestion Indian Research error: {e}")

    # 4. Global Developer Internship APIs (Filtered strictly for India context)
    try:
        i_scraper = InternshipAPIScraper(
            url="https://remotive.com", scrape_type="dynamic"
        )
        i_items = await i_scraper.fetch_real_opportunities()
        real_items.extend(i_items)
    except Exception as e:
        logger.warning(f"Live ingestion Internship API error: {e}")

    # 5. Academic & Institutional RSS Feeds
    try:
        r_scraper = RSSScraper(url="https://opportunitydesk.org", scrape_type="static")
        r_items = await r_scraper.fetch_real_opportunities()
        real_items.extend(r_items)
    except Exception as e:
        logger.warning(f"Live ingestion RSS error: {e}")

    inserted = 0
    skipped_hash = 0

    async with AsyncSessionLocal() as db:
        for item in real_items:
            # 1. Skip expired registrations
            if BaseScraper.is_expired(item.deadline):
                continue

            # 2. Skip news blogs and clickbait aggregators
            if BaseScraper.is_news_or_blog_url(
                item.source_url
            ) or BaseScraper.is_news_or_blog_url(item.application_link or ""):
                continue

            # 3. Ensure genuine India relevance
            if not BaseScraper.is_genuine_india_opportunity(
                item.title, item.description, item.institution or "", item.source_url
            ):
                continue

            content_hash = compute_content_hash(
                item.title, item.description, item.source_url
            )
            existing = (
                await db.execute(
                    select(Opportunity.id).where(
                        Opportunity.content_hash == content_hash
                    )
                )
            ).scalar_one_or_none()

            if existing:
                skipped_hash += 1
                continue

            text_lower = (item.title + " " + item.description).lower()
            domain = "unclassified"
            if any(
                k in text_lower
                for k in [
                    "ai",
                    "machine learning",
                    "data science",
                    "nlp",
                    "deep learning",
                    "robotics",
                ]
            ):
                domain = "ai_ds"
            elif any(
                k in text_lower
                for k in [
                    "code",
                    "coding",
                    "software",
                    "hackathon",
                    "web",
                    "app",
                    "dev",
                    "computer",
                ]
            ):
                domain = "cs"
            elif any(
                k in text_lower
                for k in ["electronics", "vlsi", "iot", "embedded", "hardware"]
            ):
                domain = "ece"
            elif any(
                k in text_lower
                for k in [
                    "mba",
                    "finance",
                    "marketing",
                    "management",
                    "business",
                    "case study",
                ]
            ):
                domain = "management"
            elif any(
                k in text_lower
                for k in [
                    "scholarship",
                    "fellowship",
                    "grant",
                    "bursary",
                    "dst",
                    "serb",
                    "fulbright",
                    "policy",
                ]
            ):
                domain = "govt"
            elif any(k in text_lower for k in ["bio", "health", "pharma", "medical"]):
                domain = "biotech"

            opp = Opportunity(
                title=BaseScraper.sanitize_text(item.title)[:500],
                description=BaseScraper.sanitize_text(item.description),
                institution=item.institution or "National Academic Institution",
                domain=domain,
                deadline=item.deadline,
                source_url=item.source_url,
                application_link=item.application_link or item.source_url,
                eligibility=BaseScraper.sanitize_text(
                    item.eligibility or "Open to all students"
                ),
                content_hash=content_hash,
                is_active=True,
                is_verified=True,
                classification_confidence=0.95,
            )
            db.add(opp)
            inserted += 1

        # Retire expired items. NEVER hard-delete: applications.opportunity_id and
        # autofill_logs.opportunity_id are ON DELETE CASCADE, so a DELETE here would
        # silently destroy every user's application history for past-deadline items.
        await db.execute(
            update(Opportunity)
            .where(
                Opportunity.deadline < func.now(),
                Opportunity.is_active.is_(True),
            )
            .values(is_active=False)
        )
        await db.commit()

        total_active = (
            await db.execute(
                select(func.count(Opportunity.id)).where(
                    Opportunity.is_active.is_(True)
                )
            )
        ).scalar_one()

    # Invalidate only the derived read caches. A blanket "*" would also wipe
    # refresh_jti:* (the refresh-token whitelist -> mass forced logout) and
    # blocklist:* (revoked access tokens -> revocation bypass), which live in the
    # same Redis database.
    try:
        await init_redis()
        for pattern in ("feed:*", "cache:opportunities:*", "cache:leaderboard:*"):
            await cache_delete_pattern(pattern)
        await close_redis()
    except Exception as exc:
        logger.warning(f"Live ingestion cache invalidation note: {exc}")

    return {
        "status": "success",
        "inserted": inserted,
        "skipped_hash": skipped_hash,
        "total_active": total_active,
    }


@celery_app.task(
    name="app.workers.scrape_tasks.ingest_live_opportunities_task", bind=True
)
def ingest_live_opportunities_task(self):
    """Production automated Celery task for continuous live opportunity ingestion."""
    logger.info("Starting production automated opportunity ingestion task")
    try:
        res = asyncio.run(_run_with_db_cleanup(_run_live_ingestion()))
        logger.info(f"Production opportunity ingestion complete: {res}")
        return res
    except Exception as exc:
        logger.exception(f"Production opportunity ingestion task failed: {exc}")
        return {"status": "failure", "error": str(exc)}
