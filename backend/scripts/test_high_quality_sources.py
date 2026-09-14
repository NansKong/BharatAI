"""
Test Script for High-Quality Real Opportunity Sources.
Fetches PMRF, IIT IRCC Jobs, Devfolio, AICTE Student Schemes, CSIR Fellowships, Unstop, etc.
"""

import asyncio

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TEST_TARGETS = [
    {
        "name": "PMRF (Prime Minister's Research Fellowship)",
        "url": "https://www.pmrf.in/",
        "selector": ".notice, .announcement, marquee, p, a",
        "kw": ["pmrf", "fellowship", "cycle", "application", "phd"],
    },
    {
        "name": "IIT Bombay IRCC Research Jobs",
        "url": "https://www.ircc.iitb.ac.in/IRCC-WebPage/rnd/JobOpportunities.jsp",
        "selector": "table tr, td a",
        "kw": ["project", "research", "assistant", "fellow", "engineer"],
    },
    {
        "name": "IIT Delhi IRD Vacancies",
        "url": "https://ird.iitd.ac.in/vacancies",
        "selector": "table tr, .views-row, td a",
        "kw": ["project", "assistant", "fellow", "jrf", "srf"],
    },
    {
        "name": "AICTE Student Development Schemes",
        "url": "https://www.aicte-india.org/schemes/students-development-schemes",
        "selector": "table tr, .views-row, .field-content, .card",
        "kw": [
            "pragati",
            "saksham",
            "swanath",
            "fellowship",
            "scholarship",
            "pg scholarship",
        ],
    },
    {
        "name": "CSIR HRDG Fellowships",
        "url": "https://csirhrdg.res.in/",
        "selector": "a, .news-item, li",
        "kw": ["jrf", "srf", "ra", "fellowship", "net", "award"],
    },
    {
        "name": "Devfolio Hackathons API",
        "url": "https://devfolio.co/api/hackathons?type=open&page=1&limit=10",
        "type": "json",
    },
    {
        "name": "Unstop Public Competitions Feed",
        "url": "https://unstop.com/api/public/opportunity/search-result?opportunity=competitions&per_page=15",
        "type": "json",
    },
]


async def test_target(target):
    name = target["name"]
    url = target["url"]
    print(f"\n[*] Testing target: {name} ({url})")

    try:
        async with httpx.AsyncClient(
            timeout=12.0, follow_redirects=True, verify=False
        ) as client:
            resp = await client.get(url, headers=HEADERS)
            print(f"    HTTP Status: {resp.status_code}")

            if target.get("type") == "json":
                try:
                    data = resp.json()
                    print(
                        f"    [JSON SUCCESS] Got JSON response keys: {list(data.keys()) if isinstance(data, dict) else 'list'}"
                    )
                    if "data" in data:
                        items = data["data"].get("data", []) or data["data"]
                        print(
                            f"    Found {len(items)} opportunity items in JSON payload!"
                        )
                        for item in items[:3]:
                            t = item.get("title") or item.get("name") or "Item"
                            print(f"      - {t}")
                except Exception as e:
                    print(f"    JSON Parse Error: {e}")
            else:
                soup = BeautifulSoup(resp.text, "html.parser")
                candidates = soup.select(target["selector"])
                valid = []
                for c in candidates:
                    text = c.get_text(" ", strip=True)
                    if len(text) > 15 and any(
                        k in text.lower() for k in target.get("kw", [])
                    ):
                        valid.append(text[:100])
                print(f"    Parsed {len(valid)} matching opportunity snippets!")
                for v in valid[:3]:
                    print(f"      - {v.encode('ascii', 'ignore').decode('ascii')}")
    except Exception as exc:
        print(f"    [ERR] {exc}")


async def main():
    print("============================================================")
    print("TESTING REAL HIGH-QUALITY OPPORTUNITY SOURCES")
    print("============================================================")
    for t in TEST_TARGETS:
        await test_target(t)


if __name__ == "__main__":
    asyncio.run(main())
