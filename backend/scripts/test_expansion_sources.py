"""
Expansion Sources Testing Script.
Tests fetching live opportunities from:
1. Devfolio API (Indian Developer & Web3/AI Hackathons)
2. Kaggle Competitions API / Public Feed (Data Science & AI Challenges)
3. PMRF Live Portal (Prime Minister's Research Fellowship)
4. PIB India / DST Research Notices RSS Feeds
"""

import asyncio
import xml.etree.ElementTree as ET

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}

EXPANSION_TARGETS = [
    {
        "name": "Devfolio Public Hackathons API",
        "url": "https://api.devfolio.co/api/hackathons?type=open&page=1&limit=20",
        "type": "json_devfolio",
    },
    {
        "name": "Kaggle Competitions List (Public)",
        "url": "https://www.kaggle.com/api/v1/competitions/list?group=general&sort_by=latestDeadline&page=1",
        "type": "json_kaggle",
    },
    {
        "name": "PMRF (Prime Minister's Research Fellowship Portal)",
        "url": "https://www.pmrf.in/",
        "type": "html_pmrf",
    },
    {
        "name": "AICTE Announcements & Schemes RSS/HTML",
        "url": "https://www.aicte-india.org/schemes/students-development-schemes",
        "type": "html_aicte",
    },
    {
        "name": "Opportunity Desk / Research Opportunities RSS Feed",
        "url": "https://opportunitydesk.org/category/fellowships/feed/",
        "type": "rss",
    },
]


async def test_source(target):
    name = target["name"]
    url = target["url"]
    stype = target["type"]
    print(f"\n[*] Testing Expansion Source: {name}")
    print(f"    URL: {url}")

    try:
        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True, verify=False
        ) as client:
            resp = await client.get(url, headers=HEADERS)
            print(f"    HTTP Status: {resp.status_code}")

            if resp.status_code != 200:
                print("    [NOTE] Source returned non-200 status code.")
                return

            if stype == "json_devfolio":
                try:
                    payload = resp.json()
                    result_data = payload.get("result", []) or payload.get("data", [])
                    print(
                        f"    [DEVFOLIO SUCCESS] Extracted {len(result_data)} hackathon items!"
                    )
                    for item in result_data[:3]:
                        name_str = item.get("name") or item.get("title")
                        slug = item.get("slug")
                        print(f"      - {name_str} (https://{slug}.devfolio.co)")
                except Exception as e:
                    print(f"    [DEVFOLIO PARSE ERR] {e}")

            elif stype == "json_kaggle":
                try:
                    data = resp.json()
                    print(
                        f"    [KAGGLE SUCCESS] Extracted {len(data) if isinstance(data, list) else 'dict'} items!"
                    )
                    if isinstance(data, list):
                        for item in data[:3]:
                            print(f"      - {item.get('title')} ({item.get('url')})")
                except Exception as e:
                    print(f"    [KAGGLE PARSE ERR] {e}")

            elif stype == "rss":
                try:
                    root = ET.fromstring(resp.content)
                    items = root.findall(".//item")
                    print(f"    [RSS SUCCESS] Extracted {len(items)} RSS items!")
                    for item in items[:3]:
                        title = item.findtext("title")
                        link = item.findtext("link")
                        print(f"      - {title[:70]} ({link})")
                except Exception as e:
                    print(f"    [RSS PARSE ERR] {e}")

            elif stype == "html_pmrf":
                soup = BeautifulSoup(resp.text, "html.parser")
                text_blocks = soup.find_all(["p", "div", "h2", "h3", "li"])
                pmrf_items = []
                for b in text_blocks:
                    t = b.get_text(" ", strip=True)
                    if len(t) > 20 and any(
                        k in t.lower()
                        for k in ["fellowship", "phd", "application", "pmrf", "cycle"]
                    ):
                        if t[:60] not in [x[:60] for x in pmrf_items]:
                            pmrf_items.append(t)
                print(
                    f"    [PMRF HTML SUCCESS] Extracted {len(pmrf_items)} PMRF announcements!"
                )
                for p in pmrf_items[:3]:
                    print(f"      - {p[:90].encode('ascii', 'ignore').decode('ascii')}")

            elif stype == "html_aicte":
                soup = BeautifulSoup(resp.text, "html.parser")
                links = soup.find_all("a", href=True)
                aicte_items = []
                for a in links:
                    txt = a.get_text(" ", strip=True)
                    href = a["href"]
                    if len(txt) > 15 and any(
                        k in txt.lower()
                        for k in [
                            "scheme",
                            "scholarship",
                            "pragati",
                            "saksham",
                            "fellowship",
                        ]
                    ):
                        aicte_items.append((txt, href))
                print(
                    f"    [AICTE HTML SUCCESS] Extracted {len(aicte_items)} scheme links!"
                )
                for t, h in aicte_items[:3]:
                    print(f"      - {t[:70]} ({h})")

    except Exception as exc:
        print(f"    [ERR] {exc}")


async def main():
    print("============================================================")
    print("TESTING REAL-TIME EXPANSION DATA SOURCES & RSS/API FEEDS")
    print("============================================================")
    for target in EXPANSION_TARGETS:
        await test_source(target)


if __name__ == "__main__":
    asyncio.run(main())
