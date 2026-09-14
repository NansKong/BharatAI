"""Static-page scraper using httpx + BeautifulSoup."""

from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, ScrapedOpportunity

NOISE_CONTAINERS = {"nav", "header", "footer", "aside"}
NOISE_CLASSES = {"menu", "navbar", "nav", "sidebar", "footer", "header", "breadcrumbs"}


def _is_noisy(node) -> bool:
    for parent in node.parents:
        if parent.name in NOISE_CONTAINERS:
            return True
        p_classes = set(parent.get("class", []))
        if p_classes.intersection(NOISE_CLASSES):
            return True
    return False


class StaticScraper(BaseScraper):
    """Scraper for static HTML sources."""

    async def fetch_html(self, proxy: Optional[str] = None) -> str:
        client_kwargs = {
            "timeout": self.timeout_seconds,
            "follow_redirects": True,
        }
        if proxy:
            client_kwargs["proxy"] = proxy

        async with httpx.AsyncClient(**client_kwargs) as client:
            response = await client.get(self.url)
            response.raise_for_status()
            return response.text

    def parse(self, html: str) -> list[ScrapedOpportunity]:
        soup = BeautifulSoup(html, "html.parser")
        candidates = soup.select(
            "article, .opportunity, .opportunity-card, .card, .views-row, .news-item"
        )
        if not candidates:
            body = soup.find("body")
            if body:
                candidates = [body]

        results: list[ScrapedOpportunity] = []
        seen_titles: set[str] = set()
        for node in candidates:
            if _is_noisy(node):
                continue

            title_node = node.find(["h1", "h2", "h3", "h4", "a", "strong"])
            title = BaseScraper.sanitize_text(
                title_node.get_text(" ", strip=True) if title_node else ""
            )
            description = BaseScraper.sanitize_text(node.get_text(" ", strip=True))

            if not title and description:
                title = description[:120]
            if not title or len(title) < 5:
                continue
            if title.lower() in seen_titles:
                continue
            seen_titles.add(title.lower())

            if len(description) < 25:
                continue

            link_tag = node.find("a", href=True)
            source_link = urljoin(self.url, link_tag["href"]) if link_tag else self.url
            results.append(
                ScrapedOpportunity(
                    title=title,
                    description=description,
                    source_url=source_link,
                    application_link=source_link,
                )
            )

        if results:
            return results

        fallback_title = BaseScraper.sanitize_text(
            soup.title.get_text(" ", strip=True) if soup.title else "Opportunity"
        )
        fallback_body = BaseScraper.sanitize_text(soup.get_text(" ", strip=True))
        return [
            ScrapedOpportunity(
                title=fallback_title or "Opportunity",
                description=(
                    fallback_body[:2000]
                    if fallback_body
                    else "No description available"
                ),
                source_url=self.url,
                application_link=self.url,
            )
        ]
