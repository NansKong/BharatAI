"""
Unstop API Scraper — Ingests real live hackathons, competitions, internships, and scholarships with multi-page pagination.
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

OPPORTUNITY_TYPES = [
    "internships",
    "hackathons",
    "competitions",
    "scholarships",
    "jobs",
    "quizzes",
    "workshops",
]


class UnstopAPIScraper(BaseScraper):
    """Fetches high-quality real opportunities from Unstop's public APIs across multiple pages."""

    def __init__(self, max_pages: int = 10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = max_pages

    async def fetch_real_opportunities(self) -> list[ScrapedOpportunity]:
        results: list[ScrapedOpportunity] = []
        seen_titles: set[str] = set()
        now = datetime.now(timezone.utc)

        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            for opp_type in OPPORTUNITY_TYPES:
                for page in range(1, self.max_pages + 1):
                    url = f"https://unstop.com/api/public/opportunity/search-result?opportunity={opp_type}&per_page=40&page={page}"
                    try:
                        resp = await client.get(url, headers=HEADERS)
                        if resp.status_code != 200:
                            continue
                        payload = resp.json()
                        raw_items = payload.get("data", {}).get("data", [])
                        if not raw_items:
                            break

                        for item in raw_items:
                            title = BaseScraper.sanitize_text(item.get("title") or "")
                            if not title or len(title) < 4:
                                continue

                            title_key = title.lower()
                            if title_key in seen_titles:
                                continue
                            seen_titles.add(title_key)

                            # Extract Organisation / Institution
                            org = item.get("organisation")
                            if isinstance(org, dict):
                                org_name = org.get("name") or "Unstop Partner"
                            else:
                                org_name = str(org) if org else "Unstop Partner"
                            org_name = BaseScraper.sanitize_text(org_name)

                            # Extract SEO Link
                            seo_path = item.get("seo_url") or item.get("public_url")
                            if seo_path:
                                if seo_path.startswith("http"):
                                    app_link = seo_path
                                else:
                                    app_link = (
                                        f"https://unstop.com/{seo_path.lstrip('/')}"
                                    )
                            else:
                                app_link = "https://unstop.com/competitions"

                            # Extract Eligibility tags
                            filters = item.get("filters", []) or item.get(
                                "eligibility", []
                            )
                            eligibility_list = []
                            if isinstance(filters, list):
                                for f in filters:
                                    if isinstance(f, dict) and f.get("name"):
                                        eligibility_list.append(f["name"])
                                    elif isinstance(f, str):
                                        eligibility_list.append(f)
                            eligibility_str = (
                                ", ".join(eligibility_list[:4])
                                or "Open to all students"
                            )

                            deadline_raw = item.get("end_date") or item.get(
                                "regn_requirements", {}
                            ).get("end_regn_date")
                            deadline_dt: Optional[datetime] = None
                            if deadline_raw:
                                try:
                                    clean_dt = str(deadline_raw).replace("Z", "+00:00")
                                    deadline_dt = datetime.fromisoformat(clean_dt)
                                except Exception:
                                    deadline_dt = None

                            # Filter out past/expired deadlines (only keep active & upcoming!)
                            if deadline_dt and deadline_dt < now:
                                continue

                            # Description
                            sub_title = (
                                item.get("sub_title")
                                or item.get("short_description")
                                or ""
                            )
                            desc = (
                                f"{title}. Organized by {org_name}. {sub_title}".strip()
                            )
                            if len(desc) < 30:
                                desc = f"{title} by {org_name}. Category: {opp_type.capitalize()}. Eligibility: {eligibility_str}."

                            results.append(
                                ScrapedOpportunity(
                                    title=title,
                                    description=desc,
                                    institution=org_name,
                                    deadline=deadline_dt,
                                    source_url=app_link,
                                    application_link=app_link,
                                    eligibility=eligibility_str,
                                )
                            )
                    except Exception as exc:
                        logger.warning(
                            f"Unstop fetch failed for {opp_type} page {page}: {exc}"
                        )

        return results

    async def fetch_html(self, proxy: Optional[str] = None) -> str:
        return ""

    def parse(self, html: str) -> list[ScrapedOpportunity]:
        return []
