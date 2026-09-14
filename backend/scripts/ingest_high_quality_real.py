"""
High-Quality Real Opportunity Ingestion Script for BharatAI.
Scrapes and populates the database with genuine hackathons, research grants,
fellowships, and scholarships from Unstop, Devfolio, Opportunity Desk RSS, PMRF, SERB, and top Indian institutions.
"""

import asyncio
import logging
import sys
import time

sys.path.insert(0, ".")
from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal, close_database, init_database
from app.core.redis import cache_delete_pattern, close_redis, init_redis
from app.models.opportunity import Opportunity
from app.scrapers.base import BaseScraper, ScrapedOpportunity
from app.scrapers.devfolio_api import DevfolioAPIScraper
from app.scrapers.rss_scraper import RSSScraper
from app.scrapers.unstop_api import UnstopAPIScraper

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    await init_database()
    t0 = time.monotonic()

    print("============================================================")
    print("[INGEST] RUNNING MULTI-SOURCE REAL OPPORTUNITIES EXPANSION PIPELINE")
    print("============================================================\n")

    real_items: list[ScrapedOpportunity] = []

    # 1. Fetch from Unstop API Scraper
    try:
        unstop_scraper = UnstopAPIScraper(
            url="https://unstop.com", scrape_type="dynamic"
        )
        unstop_items = await unstop_scraper.fetch_real_opportunities()
        print(f"[*] [Unstop API] Fetched {len(unstop_items)} genuine opportunities.")
        real_items.extend(unstop_items)
    except Exception as e:
        print(f"[!] Unstop fetch error: {e}")

    # 2. Fetch from Devfolio API Scraper
    try:
        devfolio_scraper = DevfolioAPIScraper(
            url="https://devfolio.co", scrape_type="dynamic"
        )
        devfolio_items = await devfolio_scraper.fetch_real_opportunities()
        print(f"[*] [Devfolio API] Fetched {len(devfolio_items)} genuine hackathons.")
        real_items.extend(devfolio_items)
    except Exception as e:
        print(f"[!] Devfolio fetch error: {e}")

    # 3. Fetch from Premier Indian Academic & Research Fellowships (IITs, IISc, DRDO, CSIR, TIFR)
    try:
        from app.scrapers.indian_research_scraper import IndianResearchScraper

        research_scraper = IndianResearchScraper(
            url="https://ird.iitd.ac.in", scrape_type="dynamic"
        )
        research_items = await research_scraper.fetch_real_opportunities()
        print(
            f"[*] [Indian Academic & Research] Fetched {len(research_items)} IIT/IISc research analyst & project internship positions."
        )
        real_items.extend(research_items)
    except Exception as e:
        print(f"[!] Indian Research fetch error: {e}")

    # 4. Fetch from Global Developer Internship APIs (Strictly filtered for India)
    try:
        from app.scrapers.internship_api import InternshipAPIScraper

        internship_scraper = InternshipAPIScraper(
            url="https://remotive.com", scrape_type="dynamic"
        )
        internship_items = await internship_scraper.fetch_real_opportunities()
        print(
            f"[*] [Internships API] Fetched {len(internship_items)} live internships & student developer roles."
        )
        real_items.extend(internship_items)
    except Exception as e:
        print(f"[!] Internship fetch error: {e}")

    # 5. Fetch from Academic Feeds
    try:
        rss_scraper = RSSScraper(
            url="https://opportunitydesk.org", scrape_type="static"
        )
        rss_items = await rss_scraper.fetch_real_opportunities()
        print(
            f"[*] [RSS Feeds] Fetched {len(rss_items)} fellowships & academic opportunities."
        )
        real_items.extend(rss_items)
    except Exception as e:
        print(f"[!] RSS fetch error: {e}")

    print(
        f"\n[TOTAL] Aggregated {len(real_items)} opportunities across all live expanded sources."
    )

    inserted_count = 0
    duplicate_count = 0
    skipped_filter_count = 0

    async with AsyncSessionLocal() as db:
        for item in real_items:
            # 1. Skip expired registrations
            if BaseScraper.is_expired(item.deadline):
                skipped_filter_count += 1
                continue

            # 2. Skip news blogs and clickbait aggregators
            if BaseScraper.is_news_or_blog_url(
                item.source_url
            ) or BaseScraper.is_news_or_blog_url(item.application_link or ""):
                skipped_filter_count += 1
                continue

            # 3. Ensure genuine India relevance
            if not BaseScraper.is_genuine_india_opportunity(
                item.title, item.description, item.institution or "", item.source_url
            ):
                skipped_filter_count += 1
                continue

            content_hash = BaseScraper.build_content_hash(
                item.title, item.description, item.source_url
            )

            # Check duplicate hash
            existing = (
                await db.execute(
                    select(Opportunity.id).where(
                        Opportunity.content_hash == content_hash
                    )
                )
            ).scalar_one_or_none()

            if existing:
                duplicate_count += 1
                continue

            # Classify Domain
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
                title=item.title,
                description=item.description,
                institution=item.institution or "National Academic Institution",
                domain=domain,
                deadline=item.deadline,
                source_url=item.source_url,
                application_link=item.application_link or item.source_url,
                eligibility=item.eligibility or "Open to all students",
                content_hash=content_hash,
                is_active=True,
                is_verified=True,
                classification_confidence=0.95,
            )
            db.add(opp)
            inserted_count += 1

        await db.commit()

        # Count total in DB
        total_in_db = (
            await db.execute(
                select(func.count(Opportunity.id)).where(
                    Opportunity.is_active.is_(True)
                )
            )
        ).scalar_one()

    # Flush Redis cache
    try:
        await init_redis()
        await cache_delete_pattern("*")
        await close_redis()
        print("[CACHE] Successfully flushed Redis cache!")
    except Exception as e:
        print(f"[WARN] Redis flush note: {e}")

    elapsed = round(time.monotonic() - t0, 2)
    print("\n============================================================")
    print("[SUMMARY] MULTI-SOURCE REAL EXPANSION INGESTION COMPLETE")
    print("============================================================")
    print(f"Time Elapsed           : {elapsed}s")
    print(f"New Genuine Items Added: {inserted_count}")
    print(f"Duplicates Skipped     : {duplicate_count}")
    print(f"Total Active DB Items  : {total_in_db}")
    print("============================================================\n")

    await close_database()


if __name__ == "__main__":
    asyncio.run(main())
