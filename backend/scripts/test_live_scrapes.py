"""
Dry-Run Live Scraper Test Script.
Tests fetching and parsing live web portals configured in MonitoredSource / SOURCE_PROFILES
without writing any data to the database.
"""

import asyncio
import sys
import time

import httpx

sys.path.insert(0, ".")
from sqlalchemy import select

from app.core.database import AsyncSessionLocal, close_database, init_database
from app.models.opportunity import MonitoredSource
from app.scrapers import build_source_scraper

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

DEFAULT_SOURCES = [
    {
        "name": "IIT Bombay Events",
        "url": "https://www.iitb.ac.in/en/events",
        "type": "static",
    },
    {
        "name": "IIT Delhi News",
        "url": "https://home.iitd.ac.in/news.php",
        "type": "static",
    },
    {
        "name": "IISc News & Events",
        "url": "https://iisc.ac.in/news-events/",
        "type": "static",
    },
    {
        "name": "AICTE Schemes & Scholarships",
        "url": "https://www.aicte-india.org/schemes",
        "type": "static",
    },
    {
        "name": "Startup India Programs",
        "url": "https://www.startupindia.gov.in/content/sih/en/government-schemes.html",
        "type": "static",
    },
    {
        "name": "DRDO Opportunities",
        "url": "https://www.drdo.gov.in/careers",
        "type": "static",
    },
    {
        "name": "Smart India Hackathon",
        "url": "https://www.sih.gov.in/",
        "type": "dynamic",
    },
    {
        "name": "Unstop Competitions",
        "url": "https://unstop.com/competitions",
        "type": "dynamic",
    },
]


async def test_single_source(
    source_name: str, source_url: str, scrape_type: str
) -> dict:
    scraper = build_source_scraper(
        source_name=source_name,
        source_url=source_url,
        scrape_type=scrape_type,
    )

    t0 = time.monotonic()
    status_code = 0
    error = None
    items = []

    try:
        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True, verify=False
        ) as client:
            resp = await client.get(source_url, headers=HEADERS)
            status_code = resp.status_code
            html = resp.text
            items = scraper.parse(html)
    except Exception as exc:
        error = str(exc)[:200]

    elapsed = round(time.monotonic() - t0, 2)
    return {
        "name": source_name,
        "url": source_url,
        "type": scrape_type,
        "status_code": status_code,
        "elapsed": elapsed,
        "items_count": len(items),
        "error": error,
        "samples": items[:3] if items else [],
    }


async def main():
    print("============================================================")
    print("[SEARCH] BHARAT AI - LIVE DRY-RUN SCRAPE TESTER")
    print("============================================================\n")

    sources_to_test = list(DEFAULT_SOURCES)

    # Try loading active sources from DB if available
    try:
        await init_database()
        async with AsyncSessionLocal() as db:
            db_sources = (
                (
                    await db.execute(
                        select(MonitoredSource).where(MonitoredSource.active.is_(True))
                    )
                )
                .scalars()
                .all()
            )
            if db_sources:
                sources_to_test = [
                    {"name": s.name, "url": s.url, "type": s.type} for s in db_sources
                ]
        await close_database()
    except Exception as e:
        print(
            f"[!] Could not load sources from DB ({e}), using default profile registry.\n"
        )

    print(f"Testing {len(sources_to_test)} monitored target sources...\n")

    results = []
    for s in sources_to_test:
        print(f"[*] Testing: {s['name']} ({s['url']})...")
        res = await test_single_source(s["name"], s["url"], s["type"])
        results.append(res)

        if res["status_code"] in (200, 301, 302):
            icon = "[OK]"
        elif res["status_code"] == 403:
            icon = "[WARN] (403 Forbidden/Cloudflare)"
        else:
            icon = "[FAIL]"

        print(
            f"   {icon} HTTP {res['status_code']} | {res['elapsed']}s | Parsed: {res['items_count']} items"
        )
        if res["error"]:
            print(f"   [ERR] Error: {res['error']}")

        for idx, sample in enumerate(res["samples"], 1):
            title_clean = (
                sample.title[:70]
                .replace("\n", " ")
                .encode("ascii", "ignore")
                .decode("ascii")
            )
            link_clean = (
                sample.source_url[:70].encode("ascii", "ignore").decode("ascii")
            )
            print(f"      - Sample #{idx}: {title_clean}")
            print(f"        Link: {link_clean}")
        print()

    print("============================================================")
    print("SUMMARY")
    print("============================================================")
    total_parsed = sum(r["items_count"] for r in results)
    successful_sources = sum(1 for r in results if r["items_count"] > 0)
    print(f"Total Sources Tested  : {len(results)}")
    print(f"Sources Yielding Data : {successful_sources} / {len(results)}")
    print(f"Total Opportunities   : {total_parsed}")
    print("============================================================")


if __name__ == "__main__":
    asyncio.run(main())
