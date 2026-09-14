"""
Live Ingestion Script for BharatAI.
Triggers scraping across active MonitoredSource entries, writes new items to DB,
and runs AI domain classification.
"""

import asyncio
import logging
import sys
import time

sys.path.insert(0, ".")
from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal, close_database, init_database
from app.models.opportunity import MonitoredSource, Opportunity
from app.workers.scrape_tasks import _scrape_source

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def run_live_ingestion():
    await init_database()
    t0 = time.monotonic()

    print("============================================================")
    print("[INGEST] STARTING LIVE DATA INGESTION PIPELINE")
    print("============================================================\n")

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

    if not sources:
        print("[!] No active sources found in database.")
        await close_database()
        return

    print(f"[*] Found {len(sources)} active monitored sources to scrape.\n")

    total_created = 0
    total_skipped_hash = 0
    total_skipped_similar = 0

    for source in sources:
        print(f"[*] Scraping source: '{source.name}' ({source.url})...")
        try:
            res = await _scrape_source(source.id)
            status = res.get("status", "unknown")
            created = res.get("created", 0)
            skipped_hash = res.get("skipped_hash", 0)
            skipped_similar = res.get("skipped_similar", 0)

            total_created += created
            total_skipped_hash += skipped_hash
            total_skipped_similar += skipped_similar

            print(
                f"    -> Status: {status} | Created: {created} new | "
                f"Skipped (Hash): {skipped_hash} | Skipped (Similar): {skipped_similar}"
            )
        except Exception as exc:
            print(f"    [ERR] Failed scraping '{source.name}': {exc}")
        print()

    # Query DB totals
    async with AsyncSessionLocal() as db:
        count_stmt = select(func.count(Opportunity.id)).where(
            Opportunity.is_active.is_(True)
        )
        total_in_db = (await db.execute(count_stmt)).scalar_one()

    elapsed = round(time.monotonic() - t0, 2)
    print("============================================================")
    print("[SUMMARY] INGESTION COMPLETED")
    print("============================================================")
    print(f"Time Elapsed            : {elapsed} seconds")
    print(f"New Opportunities Created: {total_created}")
    print(f"Duplicates Skipped      : {total_skipped_hash + total_skipped_similar}")
    print(f"Total Opportunities in DB: {total_in_db}")
    print("============================================================\n")

    await close_database()


if __name__ == "__main__":
    asyncio.run(run_live_ingestion())
