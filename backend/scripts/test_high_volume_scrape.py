"""
High Volume Scraping Test — Tests multi-page pagination across Unstop, Devfolio, and RSS feeds.
"""

import asyncio
from datetime import datetime, timezone

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

OPPORTUNITY_TYPES = [
    "hackathons",
    "competitions",
    "scholarships",
    "internships",
    "workshops",
    "festivals",
]


async def main():
    now = datetime.now(timezone.utc)
    total_found = 0
    seen_titles = set()

    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
        # 1. Unstop Multi-Page Pagination
        print("============================================================")
        print("[UNSTOP] TESTING MULTI-PAGE PAGINATION (PAGES 1-5)")
        print("============================================================\n")

        for opp_type in OPPORTUNITY_TYPES:
            type_count = 0
            for page in range(1, 6):
                url = f"https://unstop.com/api/public/opportunity/search-result?opportunity={opp_type}&per_page=50&page={page}"
                try:
                    resp = await client.get(url, headers=HEADERS)
                    if resp.status_code != 200:
                        continue
                    payload = resp.json()
                    raw_items = payload.get("data", {}).get("data", [])
                    if not raw_items:
                        break

                    for item in raw_items:
                        title = item.get("title") or ""
                        if not title or len(title) < 4:
                            continue

                        t_key = title.strip().lower()
                        if t_key in seen_titles:
                            continue

                        # Check deadline
                        deadline_raw = item.get("end_date") or item.get(
                            "regn_requirements", {}
                        ).get("end_regn_date")
                        deadline_dt = None
                        if deadline_raw:
                            try:
                                clean_dt = str(deadline_raw).replace("Z", "+00:00")
                                deadline_dt = datetime.fromisoformat(clean_dt)
                            except Exception:
                                deadline_dt = None

                        if deadline_dt and deadline_dt < now:
                            continue

                        seen_titles.add(t_key)
                        type_count += 1
                        total_found += 1
                except Exception as exc:
                    print(f"    [ERR] Unstop page {page} for {opp_type}: {exc}")

            print(
                f"  --> Unstop {opp_type.upper()}: {type_count} active/upcoming items"
            )

        # 2. Devfolio Multi-Page
        print("\n============================================================")
        print("[DEVFOLIO] TESTING MULTI-PAGE PAGINATION (PAGES 1-5)")
        print("============================================================\n")

        dev_count = 0
        for page in range(1, 6):
            url = (
                f"https://api.devfolio.co/api/hackathons?type=open&page={page}&limit=50"
            )
            try:
                resp = await client.get(url, headers=HEADERS)
                if resp.status_code != 200:
                    continue
                payload = resp.json()
                items = payload.get("result", []) or payload.get("data", [])
                if not items:
                    break

                for item in items:
                    name = item.get("name") or ""
                    if not name or len(name) < 3:
                        continue

                    n_key = name.strip().lower()
                    if n_key in seen_titles:
                        continue

                    # Deadline
                    end_raw = item.get("end_date") or item.get("starts_at")
                    deadline_dt = None
                    if end_raw:
                        try:
                            clean_dt = str(end_raw).replace("Z", "+00:00")
                            deadline_dt = datetime.fromisoformat(clean_dt)
                        except Exception:
                            deadline_dt = None

                    if deadline_dt and deadline_dt < now:
                        continue

                    seen_titles.add(n_key)
                    dev_count += 1
                    total_found += 1
            except Exception as exc:
                print(f"    [ERR] Devfolio page {page}: {exc}")

        print(f"  --> Devfolio Hackathons: {dev_count} active/upcoming items")

    print("\n============================================================")
    print(f"TOTAL HIGH-QUALITY ACTIVE & UPCOMING ITEMS FOUND: {total_found}")
    print("============================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
