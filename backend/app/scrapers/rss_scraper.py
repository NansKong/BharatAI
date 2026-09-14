"""
RSS Feed Scraper — Ingests live research fellowships, grants, and international academic opportunities.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Optional

import httpx
from app.scrapers.base import BaseScraper, ScrapedOpportunity

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

RSS_FEEDS = [
    "https://opportunitydesk.org/category/internships/feed/",
    "https://opportunitydesk.org/category/fellowships/feed/",
    "https://opportunitydesk.org/category/grants/feed/",
    "https://opportunitydesk.org/category/competitions/feed/",
    "https://www.opportunitiescircle.com/feed/",
    "https://scholarship-positions.com/feed/",
]


class RSSScraper(BaseScraper):
    """Parses standard RSS 2.0 / Atom feeds into ScrapedOpportunity items."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def fetch_real_opportunities(self) -> list[ScrapedOpportunity]:
        results: list[ScrapedOpportunity] = []
        seen_titles: set[str] = set()

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            for feed_url in RSS_FEEDS:
                try:
                    resp = await client.get(feed_url, headers=HEADERS)
                    if resp.status_code != 200:
                        continue

                    root = ET.fromstring(resp.content)
                    items = root.findall(".//item")

                    for item in items:
                        raw_title = item.findtext("title") or ""
                        title = BaseScraper.sanitize_text(raw_title)
                        if not title or len(title) < 5:
                            continue

                        t_key = title.lower()
                        if t_key in seen_titles:
                            continue
                        seen_titles.add(t_key)

                        link = item.findtext("link") or feed_url

                        # Strictly filter out news blogs, article aggregators, & non-India posts
                        if BaseScraper.is_news_or_blog_url(link):
                            continue

                        raw_desc = item.findtext("description") or ""
                        clean_desc = BaseScraper.sanitize_text(raw_desc)
                        if len(clean_desc) > 300:
                            clean_desc = clean_desc[:300] + "…"

                        inst = "Indian & Global Academic Network"
                        if " at " in title:
                            inst = title.split(" at ")[-1].split(" 20")[0].strip()
                        elif " by " in title:
                            inst = title.split(" by ")[-1].split(" 20")[0].strip()

                        if not BaseScraper.is_genuine_india_opportunity(
                            title, clean_desc, inst, link
                        ):
                            continue

                        results.append(
                            ScrapedOpportunity(
                                title=title,
                                description=f"{title}. {clean_desc}",
                                institution=BaseScraper.sanitize_text(inst),
                                deadline=None,
                                source_url=link,
                                application_link=link,
                                eligibility="Open to Indian undergraduate, postgraduate & research scholars",
                            )
                        )
                except Exception as exc:
                    logger.warning(f"RSS fetch failed for {feed_url}: {exc}")

        return results

    async def fetch_html(self, proxy: Optional[str] = None) -> str:
        return ""

    def parse(self, html: str) -> list[ScrapedOpportunity]:
        return []
