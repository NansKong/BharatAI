"""Base scraper abstraction with retry/proxy support."""

import asyncio
import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from itertools import cycle
from typing import Awaitable, Callable, Optional


@dataclass(slots=True)
class ScrapedOpportunity:
    """Normalized scrape output item."""

    title: str
    description: str
    source_url: str
    application_link: Optional[str] = None
    institution: Optional[str] = None
    deadline: Optional[datetime] = None
    eligibility: Optional[str] = None


class BaseScraper(ABC):
    """Base scraper with retry/backoff and proxy round-robin."""

    RETRY_DELAYS_SECONDS = (2, 4, 8)

    def __init__(
        self,
        url: str,
        scrape_type: str,
        proxy_list: Optional[list[str]] = None,
        timeout_seconds: float = 30.0,
        sleep_func: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.url = url
        self.scrape_type = scrape_type
        self.timeout_seconds = timeout_seconds
        self._sleep = sleep_func
        self._proxy_cycle = cycle(proxy_list) if proxy_list else None

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Normalize whitespace and remove noisy control chars."""
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        return cleaned

    @staticmethod
    def build_content_hash(title: str, description: str, source_url: str) -> str:
        payload = "|".join(
            [
                BaseScraper.sanitize_text(title).lower(),
                BaseScraper.sanitize_text(description).lower(),
                BaseScraper.sanitize_text(source_url).lower(),
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def is_news_or_blog_url(url: str) -> bool:
        """Identify news aggregators, blog sites, and clickbait article URLs."""
        if not url:
            return True
        u = url.lower()
        blacklisted_domains = [
            "opportunitydesk.org",
            "scholarship-positions.com",
            "opportunitiescircle.com",
            "youthop.com",
            "blogspot.com",
            "wordpress.com",
            "medium.com",
            "news.google.com",
            "timesofindia",
            "indiatimes.com",
            "jagranjosh.com",
            "careers360.com/news",
            "shiksha.com/news",
            "financialexpress.com",
            "livemint.com",
            "hindustantimes.com",
            "indianexpress.com",
        ]
        return any(domain in u for domain in blacklisted_domains)

    @staticmethod
    def is_expired(deadline: Optional[datetime]) -> bool:
        """Check if application deadline has already passed."""
        if not deadline:
            return False
        from datetime import timezone

        now = datetime.now(timezone.utc)
        dl = deadline if deadline.tzinfo else deadline.replace(tzinfo=timezone.utc)
        return dl < now

    @staticmethod
    def is_genuine_india_opportunity(
        title: str, description: str, institution: str, url: str
    ) -> bool:
        """Check that the opportunity is genuine (not news blog) and India-relevant."""
        if BaseScraper.is_news_or_blog_url(url):
            return False

        full_text = f"{title} {description} {institution}".lower()

        # Blacklisted spam/news terms
        if any(
            term in full_text
            for term in [
                "read article",
                "click here to read",
                "latest news on",
                "how to apply blog",
            ]
        ):
            return False

        # Positive India indicators
        india_keywords = [
            "india",
            "iit",
            "nit",
            "iisc",
            "iiit",
            "iim",
            "bits",
            "drdo",
            "isro",
            "csir",
            "tifr",
            "iiser",
            "aicte",
            "dst",
            "serb",
            "unstop",
            "devfolio",
            "bengaluru",
            "bangalore",
            "delhi",
            "mumbai",
            "hyderabad",
            "pune",
            "chennai",
            "kolkata",
            "noida",
            "gurugram",
            "gurgaon",
            "ahmedabad",
            "indian",
            "rs.",
            "inr",
            "stipend",
            "lpa",
        ]

        # Explicit non-India check (ignore purely overseas local opportunities)
        overseas_only = any(
            loc in full_text
            for loc in [
                "usa only",
                "uk resident only",
                "canada only",
                "germany only",
                "australia only",
            ]
        )
        if overseas_only:
            return False

        # Must have India context OR be from official Indian platforms/institutions
        return (
            any(k in full_text for k in india_keywords)
            or ".ac.in" in url
            or ".edu.in" in url
            or ".gov.in" in url
            or "unstop.com" in url
            or "devfolio.co" in url
        )

    def next_proxy(self) -> Optional[str]:
        if self._proxy_cycle is None:
            return None
        return next(self._proxy_cycle)

    async def scrape(self) -> list[ScrapedOpportunity]:
        """Run scrape with retries and exponential backoff."""
        last_error: Optional[Exception] = None
        attempts = len(self.RETRY_DELAYS_SECONDS) + 1

        for attempt in range(attempts):
            try:
                html = await self.fetch_html(proxy=self.next_proxy())
                return self.parse(html)
            except Exception as exc:  # pragma: no cover - exercised by tests
                last_error = exc
                if attempt >= attempts - 1:
                    break
                await self._sleep(self.RETRY_DELAYS_SECONDS[attempt])

        assert last_error is not None
        raise last_error

    @abstractmethod
    async def fetch_html(self, proxy: Optional[str] = None) -> str:
        """Return rendered HTML for the configured URL."""

    @abstractmethod
    def parse(self, html: str) -> list[ScrapedOpportunity]:
        """Parse HTML into normalized opportunities."""
