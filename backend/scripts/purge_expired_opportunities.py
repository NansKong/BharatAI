"""
Purge Expired Opportunities Script.
Deletes all opportunities from the database whose deadline has passed (past dates like 2022, 2023, 2024, 2025, or earlier in 2026).
Also flushes Redis feed cache keys.
"""

import asyncio
import sys

sys.path.insert(0, ".")
from sqlalchemy import delete, func, select, update

from app.core.database import AsyncSessionLocal, close_database, init_database
from app.core.redis import cache_delete_pattern, close_redis, init_redis
from app.models.application import Application
from app.models.opportunity import Opportunity


async def purge_expired():
    await init_database()
    print("============================================================")
    print("[CLEANUP] PURGING EXPIRED OPPORTUNITIES FROM DATABASE")
    print("============================================================\n")

    async with AsyncSessionLocal() as db:
        # Identify expired items (deadline < NOW())
        expired_filter = Opportunity.deadline < func.now()

        expired_count = (
            await db.execute(select(func.count(Opportunity.id)).where(expired_filter))
        ).scalar_one()

        print(f"[*] Found {expired_count} expired opportunity records to purge...")

        if expired_count > 0:
            # applications.opportunity_id is ON DELETE CASCADE, so deleting an
            # opportunity a student applied to destroys their application record.
            # Purge only unreferenced rows; deactivate the rest.
            referenced = select(Application.opportunity_id).distinct().scalar_subquery()

            retired = (
                await db.execute(
                    update(Opportunity)
                    .where(
                        expired_filter,
                        Opportunity.id.in_(referenced),
                        Opportunity.is_active.is_(True),
                    )
                    .values(is_active=False)
                )
            ).rowcount

            deleted = (
                await db.execute(
                    delete(Opportunity).where(
                        expired_filter, Opportunity.id.not_in(referenced)
                    )
                )
            ).rowcount
            await db.commit()
            print(f"[OK] Deleted {deleted} unreferenced expired opportunities.")
            print(
                f"[OK] Deactivated {retired} expired opportunities that have applications."
            )

        # Query remaining active & upcoming items
        remaining_count = (
            await db.execute(
                select(func.count(Opportunity.id)).where(
                    Opportunity.is_active.is_(True)
                )
            )
        ).scalar_one()

        print(
            f"[DATA] Remaining Active/Upcoming Opportunities in DB: {remaining_count}"
        )

    # Invalidate feed cache in Redis
    try:
        await init_redis()
        for pattern in ("feed:*", "cache:opportunities:*", "cache:leaderboard:*"):
            await cache_delete_pattern(pattern)
        await close_redis()
        print("[CACHE] Successfully flushed Redis feed cache!")
    except Exception as exc:
        print(f"[WARN] Redis cache note: {exc}")

    print("\n============================================================")
    print("PURGE EXPIRED COMPLETE - ONLY LIVE/UPCOMING REMAIN")
    print("============================================================\n")

    await close_database()


if __name__ == "__main__":
    asyncio.run(purge_expired())
