import asyncio

from app.scrapers.base import BaseScraper, ScrapedOpportunity
from app.scrapers.dynamic import DynamicScraper
from app.scrapers.static import StaticScraper


class FlakyScraper(BaseScraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls = 0
        self.proxies_seen: list[str | None] = []

    async def fetch_html(self, proxy=None) -> str:
        self.calls += 1
        self.proxies_seen.append(proxy)
        if self.calls < 3:
            raise RuntimeError("temporary scrape error")
        return "<html><body><article><h2>Final Opportunity</h2><p>Valid description content here.</p></article></body></html>"

    def parse(self, html: str) -> list[ScrapedOpportunity]:
        return [
            ScrapedOpportunity(
                title="Final Opportunity",
                description="Valid description content here.",
                source_url="https://example.com/final",
                application_link="https://example.com/final",
            )
        ]


def test_base_scraper_retry_backoff_and_proxy_rotation():
    delays: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        delays.append(seconds)

    scraper = FlakyScraper(
        url="https://example.com/source",
        scrape_type="static",
        proxy_list=["http://proxy1:8080", "http://proxy2:8080"],
        sleep_func=fake_sleep,
    )

    items = asyncio.run(scraper.scrape())

    assert len(items) == 1
    assert delays == [2, 4]
    assert scraper.proxies_seen == [
        "http://proxy1:8080",
        "http://proxy2:8080",
        "http://proxy1:8080",
    ]


def test_static_scraper_parse_extracts_multiple_items():
    html = """
    <html>
      <body>
        <article>
          <h2>IIT Bombay Fellowship</h2>
          <p>Apply for this fellowship opportunity for students.</p>
          <a href="/fellowship">Apply</a>
        </article>
        <article>
          <h2>DRDO Internship</h2>
          <p>Research internship with defence labs and stipends.</p>
          <a href="https://drdo.gov.in/apply">Details</a>
        </article>
      </body>
    </html>
    """
    scraper = StaticScraper(
        url="https://example.com/opportunities", scrape_type="static"
    )
    items = scraper.parse(html)

    assert len(items) == 2
    assert items[0].title == "IIT Bombay Fellowship"
    assert items[0].source_url == "https://example.com/fellowship"
    assert items[1].source_url == "https://drdo.gov.in/apply"


def test_dynamic_scraper_parse_reuses_static_parser():
    html = """
    <html>
      <body>
        <article>
          <h3>Startup India Program</h3>
          <p>Funding and mentorship program for early-stage founders.</p>
        </article>
      </body>
    </html>
    """
    scraper = DynamicScraper(url="https://startupindia.gov.in", scrape_type="dynamic")
    items = scraper.parse(html)

    assert len(items) == 1
    assert items[0].title == "Startup India Program"
