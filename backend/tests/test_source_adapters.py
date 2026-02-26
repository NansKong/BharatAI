from pathlib import Path

import pytest
from app.scrapers.sources import (ProfiledDynamicScraper,
                                  ProfiledStaticScraper, build_source_scraper,
                                  get_source_profile)
from app.scrapers.static import StaticScraper

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "scrapers"


@pytest.mark.parametrize(
    "fixture_name,source_name,source_url,scrape_type,expected_title,expected_link",
    [
        (
            "iit_bombay_events.html",
            "IIT Bombay Events",
            "https://www.iitb.ac.in/new/content/events",
            "static",
            "Summer Research Internship 2026",
            "https://www.iitb.ac.in/events/sri-2026",
        ),
        (
            "iit_delhi_opportunities.html",
            "IIT Delhi Opportunities",
            "https://home.iitd.ac.in/opportunities",
            "static",
            "IIT Delhi Innovation Fellowship",
            "https://home.iitd.ac.in/opportunities/innovation-fellowship",
        ),
        (
            "iisc_announcements.html",
            "IISc Announcements",
            "https://www.iisc.ac.in/announcements/",
            "static",
            "IISc Advanced Research Call",
            "https://www.iisc.ac.in/announcements/research-call",
        ),
        (
            "aicte_scholarships.html",
            "AICTE Scholarships",
            "https://www.aicte-india.org/schemes",
            "static",
            "AICTE National Merit Scholarship",
            "https://www.aicte-india.org/schemes/merit-scholarship",
        ),
        (
            "startup_india_programs.html",
            "Startup India Programs",
            "https://startupindia.gov.in/content/sih/en/initiatives.html",
            "static",
            "Startup India Seed Fund Program",
            "https://startupindia.gov.in/programs/seed-fund",
        ),
        (
            "drdo_recruitment.html",
            "DRDO Careers",
            "https://www.drdo.gov.in/careers",
            "static",
            "DRDO Junior Research Fellowship",
            "https://www.drdo.gov.in/careers/jrf-2026",
        ),
        (
            "sih_challenges.html",
            "Smart India Hackathon",
            "https://www.sih.gov.in/",
            "dynamic",
            "Smart India Hackathon Open Challenge",
            "https://www.sih.gov.in/challenge/open-2026",
        ),
        (
            "unstop_competitions.html",
            "Unstop Competitions",
            "https://unstop.com/hackathons",
            "dynamic",
            "Unstop AI Sprint Competition",
            "https://unstop.com/competition/ai-sprint",
        ),
    ],
)
def test_source_specific_adapters_parse_fixtures(
    fixture_name: str,
    source_name: str,
    source_url: str,
    scrape_type: str,
    expected_title: str,
    expected_link: str,
):
    html = (FIXTURE_DIR / fixture_name).read_text(encoding="utf-8")
    scraper = build_source_scraper(
        source_name=source_name,
        source_url=source_url,
        scrape_type=scrape_type,
    )
    profile = get_source_profile(source_name=source_name, source_url=source_url)

    assert profile is not None
    if scrape_type == "dynamic":
        assert isinstance(scraper, ProfiledDynamicScraper)
    else:
        assert isinstance(scraper, ProfiledStaticScraper)

    items = scraper.parse(html)
    assert len(items) == 1
    assert items[0].title == expected_title
    assert items[0].source_url == expected_link


def test_unknown_source_falls_back_to_generic_scraper():
    scraper = build_source_scraper(
        source_name="Unknown Institute Feed",
        source_url="https://example.org/feed",
        scrape_type="static",
    )
    assert isinstance(scraper, StaticScraper)
    assert not isinstance(scraper, ProfiledStaticScraper)
