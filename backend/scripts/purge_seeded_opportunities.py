"""
Purge Seeded Opportunities Script.
Deletes all static/mock seeded opportunities from the database, leaving only real live scraped opportunities.
Also flushes Redis feed cache keys.
"""

import asyncio
import sys

sys.path.insert(0, ".")
from sqlalchemy import delete, func, or_, select

from app.core.database import AsyncSessionLocal, close_database, init_database
from app.core.redis import cache_delete_pattern
from app.models.opportunity import Opportunity


async def purge_seeded():
    await init_database()
    print("============================================================")
    print("[CLEANUP] PURGING SEEDED MOCK OPPORTUNITIES FROM DATABASE")
    print("============================================================\n")

    async with AsyncSessionLocal() as db:
        # Identify seeded items
        seeded_filter = or_(
            Opportunity.source_id.is_(None),
            Opportunity.source_url.ilike("%example.com%"),
            Opportunity.content_hash.ilike("seed_hash_%"),
        )

        seeded_count = (
            await db.execute(select(func.count(Opportunity.id)).where(seeded_filter))
        ).scalar_one()

        print(f"[*] Found {seeded_count} seeded opportunity records to purge...")

        if seeded_count > 0:
            stmt = delete(Opportunity).where(seeded_filter)
            await db.execute(stmt)
            await db.commit()
            print(f"[OK] Successfully deleted {seeded_count} seeded opportunities!")

        # Query remaining live items
        live_count = (
            await db.execute(
                select(func.count(Opportunity.id)).where(
                    Opportunity.is_active.is_(True)
                )
            )
        ).scalar_one()

        print(f"[DATA] Remaining Live Scraped Opportunities in DB: {live_count}")

    # Invalidate feed cache in Redis
    try:
        await cache_delete_pattern("feed:*")
        print("[CACHE] Invalidated Redis feed cache (feed:*).")
    except Exception as exc:
        print(f"[WARN] Redis cache invalidation note: {exc}")

    print("\n============================================================")
    print("PURGE COMPLETE - ONLY LIVE OPPORTUNITIES REMAIN")
    print("============================================================\n")

    await close_database()


if __name__ == "__main__":
    asyncio.run(purge_seeded())
