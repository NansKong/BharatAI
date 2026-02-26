"""Source-specific scraper adapters and profile registry."""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

from app.scrapers.base import BaseScraper, ScrapedOpportunity
from app.scrapers.dynamic import DynamicScraper
from app.scrapers.static import StaticScraper
from bs4 import BeautifulSoup


@dataclass(frozen=True, slots=True)
class SourceProfile:
    key: str
    scrape_type: str
    name_markers: tuple[str, ...]
    url_markers: tuple[str, ...]
    item_selector: str
    title_selector: str
    description_selector: str
    link_selector: str = "a[href]"


SOURCE_PROFILES: tuple[SourceProfile, ...] = (
    SourceProfile(
        key="iit_bombay_events",
        scrape_type="static",
        name_markers=("iit bombay",),
        url_markers=("iitb.ac.in",),
        item_selector=".iitb-event",
        title_selector="h2, h3, .title",
        description_selector=".summary, p",
    ),
    SourceProfile(
        key="iit_delhi_opportunities",
        scrape_type="static",
        name_markers=("iit delhi",),
        url_markers=("iitd.ac.in",),
        item_selector=".iitd-opportunity",
        title_selector="h2, h3, .title",
        description_selector=".summary, p",
    ),
    SourceProfile(
        key="iisc_announcements",
        scrape_type="static",
        name_markers=("iisc",),
        url_markers=("iisc.ac.in",),
        item_selector=".iisc-announcement",
        title_selector="h2, h3, .title",
        description_selector=".summary, p",
    ),
    SourceProfile(
        key="aicte_scholarships",
        scrape_type="static",
        name_markers=("aicte",),
        url_markers=("aicte-india.org",),
        item_selector=".aicte-scheme",
        title_selector="h2, h3, .title",
        description_selector=".summary, p",
    ),
    SourceProfile(
        key="startup_india_programs",
        scrape_type="static",
        name_markers=("startup india",),
        url_markers=("startupindia.gov.in",),
        item_selector=".startup-program",
        title_selector="h2, h3, .title",
        description_selector=".summary, p",
    ),
    SourceProfile(
        key="drdo_recruitment",
        scrape_type="static",
        name_markers=("drdo",),
        url_markers=("drdo.gov.in",),
        item_selector=".drdo-opening",
        title_selector="h2, h3, .title",
        description_selector=".summary, p",
    ),
    SourceProfile(
        key="sih_portal",
        scrape_type="dynamic",
        name_markers=("smart india hackathon", "sih"),
        url_markers=("sih.gov.in",),
        item_selector=".sih-challenge",
        title_selector="h2, h3, .title",
        description_selector=".summary, p",
    ),
    SourceProfile(
        key="unstop_competitions",
        scrape_type="dynamic",
        name_markers=("unstop",),
        url_markers=("unstop.com",),
        item_selector=".unstop-card",
        title_selector="h2, h3, .title",
        description_selector=".summary, p",
    ),
)


def _normalize(value: str) -> str:
    return BaseScraper.sanitize_text(value).lower()


def get_source_profile(source_name: str, source_url: str) -> Optional[SourceProfile]:
    normalized_name = _normalize(source_name)
    normalized_url = _normalize(source_url)

    for profile in SOURCE_PROFILES:
        by_name = any(marker in normalized_name for marker in profile.name_markers)
        by_url = any(marker in normalized_url for marker in profile.url_markers)
        if by_name or by_url:
            return profile
    return None


def _parse_with_profile(
    html: str, base_url: str, profile: SourceProfile
) -> list[ScrapedOpportunity]:
    soup = BeautifulSoup(html, "html.parser")
    nodes = soup.select(profile.item_selector)
    if not nodes:
        return []

    results: list[ScrapedOpportunity] = []
    seen: set[str] = set()
    for node in nodes:
        title_node = node.select_one(profile.title_selector)
        desc_node = node.select_one(profile.description_selector)
        link_node = node.select_one(profile.link_selector)

        title = BaseScraper.sanitize_text(
            title_node.get_text(" ", strip=True) if title_node else ""
        )
        description = BaseScraper.sanitize_text(
            desc_node.get_text(" ", strip=True)
            if desc_node
            else node.get_text(" ", strip=True)
        )
        if not title:
            continue
        title_key = title.lower()
        if title_key in seen:
            continue
        seen.add(title_key)
        if len(description) < 20:
            continue

        source_url = base_url
        if link_node and link_node.get("href"):
            source_url = urljoin(base_url, link_node["href"])

        results.append(
            ScrapedOpportunity(
                title=title,
                description=description,
                source_url=source_url,
                application_link=source_url,
            )
        )
    return results


class ProfiledStaticScraper(StaticScraper):
    def __init__(self, *args, profile: SourceProfile, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile

    def parse(self, html: str) -> list[ScrapedOpportunity]:
        parsed = _parse_with_profile(html, self.url, self.profile)
        if parsed:
            return parsed
        return super().parse(html)


class ProfiledDynamicScraper(DynamicScraper):
    def __init__(self, *args, profile: SourceProfile, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = profile

    def parse(self, html: str) -> list[ScrapedOpportunity]:
        parsed = _parse_with_profile(html, self.url, self.profile)
        if parsed:
            return parsed
        return super().parse(html)


def build_source_scraper(
    *,
    source_name: str,
    source_url: str,
    scrape_type: str,
    proxy_list: Optional[list[str]] = None,
    timeout_seconds: float = 30.0,
) -> BaseScraper:
    profile = get_source_profile(source_name=source_name, source_url=source_url)
    common_kwargs = {
        "url": source_url,
        "scrape_type": scrape_type,
        "proxy_list": proxy_list,
        "timeout_seconds": timeout_seconds,
    }

    effective_type = scrape_type
    if profile is not None:
        effective_type = profile.scrape_type

    if effective_type == "dynamic":
        if profile is not None:
            return ProfiledDynamicScraper(profile=profile, **common_kwargs)
        return DynamicScraper(**common_kwargs)

    if profile is not None:
        return ProfiledStaticScraper(profile=profile, **common_kwargs)
    return StaticScraper(**common_kwargs)
