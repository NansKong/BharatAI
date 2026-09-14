"""
Purge and Re-Ingest Genuine Live India Opportunities.
Removes:
- All static seed mock data.
- All expired listings (deadline < now).
- All news blogs & article aggregators.
- All non-India or overseas-only listings.

Ingests:
- 100% real-time Unstop India hackathons, internships, jobs, scholarships.
- Devfolio India open hackathons & grants.
- IIT Delhi, IISc Bangalore, IIT Bombay, DRDO, CSIR, TIFR research analyst & project associate internships.
- Genuine direct ATS application links.
"""

import asyncio
import sys
from datetime import datetime, timezone

sys.path.insert(0, ".")
from app.core.database import AsyncSessionLocal, close_database, init_database
from app.core.redis import cache_delete_pattern, close_redis, init_redis
from app.models.opportunity import Opportunity
from app.scrapers.base import BaseScraper
from app.workers.scrape_tasks import _run_live_ingestion
from sqlalchemy import delete, func, select


async def purge_and_reingest():
    await init_database()
    print("============================================================")
    print("[HARDENING] PURGING NON-INDIA, EXPIRED, SEEDED & BLOG ITEMS")
    print("============================================================\n")

    async with AsyncSessionLocal() as db:
        # Fetch all current items
        all_opps = (await db.execute(select(Opportunity))).scalars().all()
        to_delete_ids = []
        now = datetime.now(timezone.utc)

        for opp in all_opps:
            # 1. Seeded items
            is_seeded = (
                opp.source_id is None
                or "example.com" in (opp.source_url or "")
                or (opp.content_hash or "").startswith("seed_hash_")
            )
            # 2. Expired items
            is_exp = False
            if opp.deadline:
                dl = (
                    opp.deadline
                    if opp.deadline.tzinfo
                    else opp.deadline.replace(tzinfo=timezone.utc)
                )
                if dl < now:
                    is_exp = True

            # 3. News blog URLs
            is_blog = BaseScraper.is_news_or_blog_url(
                opp.source_url or ""
            ) or BaseScraper.is_news_or_blog_url(opp.application_link or "")

            # 4. Non-India or low quality
            is_not_india = not BaseScraper.is_genuine_india_opportunity(
                opp.title, opp.description, opp.institution or "", opp.source_url or ""
            )

            if is_seeded or is_exp or is_blog or is_not_india:
                to_delete_ids.append(opp.id)

        print(
            f"[*] Found {len(to_delete_ids)} records to purge (seeded/expired/news blogs/non-India)..."
        )
        if to_delete_ids:
            await db.execute(
                delete(Opportunity).where(Opportunity.id.in_(to_delete_ids))
            )
            await db.commit()
            print(
                f"[OK] Successfully purged {len(to_delete_ids)} non-conforming items."
            )

    print("\n============================================================")
    print("[INGESTION] RUNNING LIVE INDIA REAL-TIME INGESTION PIPELINE")
    print("============================================================\n")

    # Run live pipeline
    res = await _run_live_ingestion()
    print(f"[RESULTS] Ingestion output: {res}")

    async with AsyncSessionLocal() as db:
        total_active = (
            await db.execute(
                select(func.count(Opportunity.id)).where(
                    Opportunity.is_active.is_(True)
                )
            )
        ).scalar_one()
        print(
            f"\n[SUMMARY] Total Genuine Active India Opportunities in DB: {total_active}"
        )

    try:
        await init_redis()
        await cache_delete_pattern("feed:*")
        print("[CACHE] Flushed Redis feed cache (feed:*).")
        await close_redis()
    except Exception as exc:
        print(f"[WARN] Redis flush note: {exc}")

    await close_database()
    print("\n============================================================")
    print("PIPELINE COMPLETE - 100% GENUINE INDIA LIVE DATA READY")
    print("============================================================\n")


if __name__ == "__main__":
    asyncio.run(purge_and_reingest())
