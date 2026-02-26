"""Dynamic-page scraper using Playwright."""

from typing import Optional

from app.scrapers.base import BaseScraper, ScrapedOpportunity
from app.scrapers.static import StaticScraper
from playwright.async_api import async_playwright


class DynamicScraper(BaseScraper):
    """Scraper for JavaScript-rendered pages."""

    async def fetch_html(self, proxy: Optional[str] = None) -> str:
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
