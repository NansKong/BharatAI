"""Dynamic-page scraper with Playwright support and HTTP fallback."""

import logging
from typing import Optional

from app.scrapers.base import BaseScraper, ScrapedOpportunity
from app.scrapers.static import StaticScraper

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class DynamicScraper(BaseScraper):
    """Scraper for JavaScript-rendered pages with Playwright or httpx fallback."""

    async def fetch_html(self, proxy: Optional[str] = None) -> str:
        if not PLAYWRIGHT_AVAILABLE:
            logger.info(
                "Playwright not installed, falling back to static fetcher for %s",
                self.url,
            )
            static_scraper = StaticScraper(
                url=self.url,
                scrape_type=self.scrape_type,
                timeout_seconds=self.timeout_seconds,
            )
            return await static_scraper.fetch_html(proxy=proxy)

        launch_kwargs = {"headless": True}
        if proxy:
            launch_kwargs["proxy"] = {"server": proxy}

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(**launch_kwargs)
            try:
                page = await browser.new_page()
                await page.goto(
                    self.url,
                    wait_until="networkidle",
                    timeout=int(self.timeout_seconds * 1000),
                )
                return await page.content()
            finally:
                await browser.close()

    def parse(self, html: str) -> list[ScrapedOpportunity]:
        # Reuse static HTML parser for extracted DOM content.
        return StaticScraper(url=self.url, scrape_type=self.scrape_type).parse(html)
