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
