"""
Fix Monitored Source URLs in PostgreSQL Database.
Updates monitored_sources rows with clean, verified live target URLs.
"""

import asyncio
import sys

sys.path.insert(0, ".")
from app.core.database import AsyncSessionLocal, close_database, init_database
from app.models.opportunity import MonitoredSource
from sqlalchemy import select

URL_UPDATES = {
    "IIT Bombay Events": "https://www.iitb.ac.in/en/events",
    "IIT Delhi Opportunities": "https://home.iitd.ac.in/news.php",
    "IISc Announcements": "https://www.iisc.ac.in/announcements/",
    "AICTE Scholarships": "https://www.aicte-india.org/schemes",
    "Startup India Programs": "https://www.startupindia.gov.in/content/sih/en/government-schemes.html",
    "DRDO Recruitment": "https://www.drdo.gov.in/",
    "Smart India Hackathon": "https://www.sih.gov.in/",
    "Unstop Competitions": "https://unstop.com/competitions",
}


async def main():
    await init_database()
    async with AsyncSessionLocal() as db:
        sources = (await db.execute(select(MonitoredSource))).scalars().all()
        updated_count = 0

        for s in sources:
            if s.name in URL_UPDATES:
                s.url = URL_UPDATES[s.name]
                s.active = True
                s.failure_count = 0
                s.last_error = None
                updated_count += 1

        await db.commit()
        print(
            f"✅ Successfully updated and re-activated {updated_count} monitored sources in DB!"
        )

    await close_database()


if __name__ == "__main__":
    asyncio.run(main())
