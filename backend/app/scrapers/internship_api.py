"""
Global Internship & Developer Opportunity API Scraper.
Scrapes live internships, software engineering fellowships, entry-level research roles, and student builder positions from Remotive & Arbeitnow public APIs.
"""

import logging
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


class InternshipAPIScraper(BaseScraper):
    """Fetches high-quality live student internships, developer roles, and research positions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def fetch_real_opportunities(self) -> list[ScrapedOpportunity]:
        results: list[ScrapedOpportunity] = []
        seen_titles: set[str] = set()

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            # 1. Remotive API
            try:
                url = "https://remotive.com/api/remote-jobs?limit=100"
                resp = await client.get(url, headers=HEADERS)
                if resp.status_code == 200:
                    jobs = resp.json().get("jobs", [])
                    for job in jobs:
                        title = BaseScraper.sanitize_text(job.get("title") or "")
                        category = (job.get("category") or "").lower()
                        title_lower = title.lower()

                        # Filter for internships, entry-level, student, software, AI, ML, design, or data roles
                        is_internship = any(
                            k in title_lower
                            for k in [
                                "intern",
                                "trainee",
                                "junior",
                                "graduate",
                                "associate",
                                "fellow",
                                "apprentice",
                                "student",
                                "ai",
                                "data science",
                                "software",
                                "developer",
                            ]
                        )
                        if (
                            not is_internship
                            and "software" not in category
                            and "data" not in category
                        ):
                            continue

                        if not title or len(title) < 4:
                            continue

                        if title_lower in seen_titles:
                            continue
                        seen_titles.add(title_lower)

                        company = BaseScraper.sanitize_text(
                            job.get("company_name") or "Global Tech Portal"
                        )
                        app_url = job.get("url") or "https://remotive.com"
                        job_type = job.get("job_type") or "Internship / Entry-Level"

                        desc_raw = BaseScraper.sanitize_text(
                            job.get("description") or ""
                        )
                        if len(desc_raw) > 350:
                            desc_raw = desc_raw[:350] + "…"
                        desc = f"{title} at {company}. Type: {job_type}. {desc_raw}"

                        results.append(
                            ScrapedOpportunity(
                                title=title[:500],
                                description=desc,
                                institution=company,
                                deadline=None,  # Open deadline
                                source_url=app_url,
                                application_link=app_url,
                                eligibility="Open to students, graduates, & early career developers",
                            )
                        )
            except Exception as exc:
                logger.warning(f"Remotive API scrape failed: {exc}")

            # 2. Arbeitnow Public Job & Internship API
            try:
                url = "https://www.arbeitnow.com/api/job-board-api"
                resp = await client.get(url, headers=HEADERS)
                if resp.status_code == 200:
                    jobs = resp.json().get("data", [])
                    for job in jobs:
                        title = BaseScraper.sanitize_text(job.get("title") or "")
                        title_lower = title.lower()

                        is_target = any(
                            k in title_lower
                            for k in [
                                "intern",
                                "trainee",
                                "junior",
                                "graduate",
                                "working student",
                                "werkstudent",
                                "fellow",
                                "research",
                                "developer",
                                "engineer",
                                "ai",
                                "data",
                            ]
                        )
                        if not is_target:
                            continue

                        if not title or len(title) < 4 or title_lower in seen_titles:
                            continue
                        seen_titles.add(title_lower)

                        company = BaseScraper.sanitize_text(
                            job.get("company_name") or "Global Industry Partner"
                        )
                        app_url = job.get("url") or "https://www.arbeitnow.com"

                        desc_raw = BaseScraper.sanitize_text(
                            job.get("description") or ""
                        )
                        if len(desc_raw) > 350:
                            desc_raw = desc_raw[:350] + "…"
                        desc = f"{title} at {company}. {desc_raw}"

                        results.append(
                            ScrapedOpportunity(
                                title=title[:500],
                                description=desc,
                                institution=company,
                                deadline=None,
                                source_url=app_url,
                                application_link=app_url,
                                eligibility="Open to computer science, engineering, & research students",
                            )
                        )
            except Exception as exc:
                logger.warning(f"Arbeitnow API scrape failed: {exc}")

        return results

    async def fetch_html(self, proxy: Optional[str] = None) -> str:
        return ""

    def parse(self, html: str) -> list[ScrapedOpportunity]:
        return []
