import asyncio
import sys

sys.path.insert(0, ".")
from app.core.database import AsyncSessionLocal, close_database
from app.models.opportunity import Opportunity
from sqlalchemy import select


async def main():
    async with AsyncSessionLocal() as db:
        rows = (
            (
                await db.execute(
                    select(Opportunity)
                    .order_by(Opportunity.created_at.desc())
                    .limit(15)
                )
            )
            .scalars()
            .all()
        )
        print("\n============================================================")
        print(f"[DATA] RECENTLY INGESTED OPPORTUNITIES IN DATABASE ({len(rows)} ITEMS)")
        print("============================================================\n")
        for idx, r in enumerate(rows, 1):
            title = r.title[:75].encode("ascii", "ignore").decode("ascii")
            inst = (
                (r.institution or "Unknown").encode("ascii", "ignore").decode("ascii")
            )
            print(f" {idx:2d}. [{inst}] {title}")
            print(f"     Domain: {r.domain} | Verified: {r.is_verified}")
            print(f"     URL   : {r.source_url[:75]}")
            print()
    await close_database()


if __name__ == "__main__":
    asyncio.run(main())
