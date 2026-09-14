"""
Test UnstopAPIScraper output.
"""

import asyncio
import sys

sys.path.insert(0, ".")
from app.scrapers.unstop_api import UnstopAPIScraper


async def main():
    scraper = UnstopAPIScraper(url="https://unstop.com", scrape_type="dynamic")
    items = await scraper.fetch_real_opportunities()
    print("\n============================================================")
    print(f"[UNSTOP API] SCRAPER RETURNED {len(items)} REAL OPPORTUNITIES")
    print("============================================================\n")
    for idx, item in enumerate(items, 1):
        title = item.title[:75].encode("ascii", "ignore").decode("ascii")
        inst = (item.institution or "Unknown").encode("ascii", "ignore").decode("ascii")
        elig = (item.eligibility or "All").encode("ascii", "ignore").decode("ascii")
        dl = item.deadline.strftime("%Y-%m-%d") if item.deadline else "No deadline"
        print(f" {idx:2d}. [{inst}] {title}")
        print(f"     Deadline: {dl} | Eligibility: {elig}")
        print(f"     Link    : {item.application_link[:75]}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
