"""
Devfolio API Scraper — Ingests live developer, AI, and Web3 hackathons from Devfolio India with multi-page pagination.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.scrapers.base import BaseScraper, ScrapedOpportunity

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


class DevfolioAPIScraper(BaseScraper):
    """Scrapes open hackathons from Devfolio's public API across multiple pages."""

    def __init__(self, max_pages: int = 10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = max_pages

    async def fetch_real_opportunities(self) -> list[ScrapedOpportunity]:
        results: list[ScrapedOpportunity] = []
        seen_titles: set[str] = set()
        now = datetime.now(timezone.utc)

        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            for page in range(1, self.max_pages + 1):
                url = f"https://api.devfolio.co/api/hackathons?type=open&page={page}&limit=50"
                try:
                    resp = await client.get(url, headers=HEADERS)
                    if resp.status_code != 200:
                        continue

                    payload = resp.json()
                    items = payload.get("result", []) or payload.get("data", [])
                    if not items:
                        break

                    for item in items:
                        name = BaseScraper.sanitize_text(item.get("name") or "")
                        if not name or len(name) < 3:
                            continue

                        name_key = name.lower()
                        if name_key in seen_titles:
                            continue
                        seen_titles.add(name_key)

                        slug = item.get("slug") or ""
                        app_link = (
                            f"https://{slug}.devfolio.co"
                            if slug
                            else "https://devfolio.co/hackathons"
                        )

                        tagline = (
                            item.get("tagline")
                            or item.get("description")
                            or "National Developer & AI Hackathon"
                        )
                        desc = f"{name}. {tagline}. Platform: Devfolio."

                        # Institution / Organizer
                        org = (
                            item.get("organisation_name")
                            or item.get("location")
                            or "Devfolio Partner Community"
                        )
                        org_name = BaseScraper.sanitize_text(org)

                        # Deadline
                        end_raw = item.get("end_date") or item.get("starts_at")
                        deadline_dt: Optional[datetime] = None
                        if end_raw:
                            try:
                                clean_dt = str(end_raw).replace("Z", "+00:00")
                                deadline_dt = datetime.fromisoformat(clean_dt)
                            except Exception:
                                deadline_dt = None

                        # Skip past deadlines
                        if deadline_dt and deadline_dt < now:
                            continue

                        results.append(
                            ScrapedOpportunity(
                                title=name,
                                description=desc,
                                institution=org_name,
                                deadline=deadline_dt,
                                source_url=app_link,
                                application_link=app_link,
                                eligibility="Open to all developers, engineering & CS students",
                            )
                        )
                except Exception as exc:
                    logger.warning(f"Devfolio API scrape failed for page {page}: {exc}")

        return results

    async def fetch_html(self, proxy: Optional[str] = None) -> str:
        return ""

    def parse(self, html: str) -> list[ScrapedOpportunity]:
        return []
