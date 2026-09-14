import asyncio
import sys

sys.path.insert(0, ".")
from sqlalchemy import delete, or_

from app.core.database import AsyncSessionLocal, close_database, init_database
from app.models.opportunity import Opportunity


async def main():
    await init_database()
    async with AsyncSessionLocal() as db:
        stmt = delete(Opportunity).where(
            or_(
                Opportunity.title.ilike("%Login Dashboard%"),
                Opportunity.title.ilike("%English %"),
            )
        )
        await db.execute(stmt)
        await db.commit()
        print("[OK] Purged raw header noise records.")
    await close_database()


if __name__ == "__main__":
    asyncio.run(main())
