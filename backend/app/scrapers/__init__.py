"""Scraper framework exports."""

from app.scrapers.base import BaseScraper, ScrapedOpportunity
from app.scrapers.dedup import (compute_content_hash, find_title_duplicate,
                                title_similarity)
from app.scrapers.dynamic import DynamicScraper
from app.scrapers.sources import (SOURCE_PROFILES, ProfiledDynamicScraper,
                                  ProfiledStaticScraper, build_source_scraper,
                                  get_source_profile)
from app.scrapers.static import StaticScraper

__all__ = [
    "BaseScraper",
    "DynamicScraper",
    "ProfiledDynamicScraper",
    "ProfiledStaticScraper",
    "ScrapedOpportunity",
    "SOURCE_PROFILES",
    "StaticScraper",
    "build_source_scraper",
    "compute_content_hash",
    "find_title_duplicate",
    "get_source_profile",
    "title_similarity",
]
