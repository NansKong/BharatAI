"""
Inspect Unstop Public API JSON Payload.
"""

import asyncio

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

UNSTOP_URLS = [
    "https://unstop.com/api/public/opportunity/search-result?opportunity=competitions&per_page=10",
    "https://unstop.com/api/public/opportunity/search-result?opportunity=hackathons&per_page=10",
    "https://unstop.com/api/public/opportunity/search-result?opportunity=scholarships&per_page=10",
]


async def main():
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for url in UNSTOP_URLS:
            print("\n============================================================")
            print(f"FETCHING: {url}")
            print("============================================================\n")
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code == 200:
                payload = resp.json()
                items = payload.get("data", {}).get("data", [])
                print(f"Extracted {len(items)} items!")
                for idx, item in enumerate(items[:5], 1):
                    title = item.get("title")
                    org = (
                        item.get("organisation", {}).get("name")
                        if isinstance(item.get("organisation"), dict)
                        else item.get("organisation")
                    )
                    seo_url = item.get("seo_url") or item.get("public_url")
                    deadline = item.get("end_date") or item.get(
                        "regn_requirements", {}
                    ).get("end_regn_date")
                    eligibility = item.get("eligibility", "") or item.get("filters", [])

                    print(f" Item #{idx}:")
                    print(f"   Title       : {title}")
                    print(f"   Organisation: {org}")
                    print(
                        f"   URL         : https://unstop.com/{seo_url}"
                        if seo_url
                        else f"   URL: {item.get('site_url')}"
                    )
                    print(f"   Deadline    : {deadline}")
                    print(f"   Eligibility : {eligibility}")
                    print()


if __name__ == "__main__":
    asyncio.run(main())
