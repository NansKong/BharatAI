"""
Test filtering active/upcoming Unstop items.
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

UNSTOP_URLS = [
    "https://unstop.com/api/public/opportunity/search-result?opportunity=hackathons&per_page=30",
    "https://unstop.com/api/public/opportunity/search-result?opportunity=competitions&per_page=30",
    "https://unstop.com/api/public/opportunity/search-result?opportunity=scholarships&per_page=30",
    "https://unstop.com/api/public/opportunity/search-result?opportunity=internships&per_page=30",
]


async def main():
    now = datetime.now(timezone.utc)
    total_valid = 0

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for url in UNSTOP_URLS:
            opp_type = url.split("opportunity=")[1].split("&")[0]
            print("\n============================================================")
            print(f"FETCHING UPCOMING & LIVE: {opp_type.upper()}")
            print("============================================================\n")
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code == 200:
                payload = resp.json()
                raw_items = payload.get("data", {}).get("data", [])

                valid_count = 0
                for item in raw_items:
                    title = item.get("title", "")
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

                    # Strict filter: Exclude past deadlines!
                    if deadline_dt and deadline_dt < now:
                        continue

                    valid_count += 1
                    total_valid += 1
                    dl_str = (
                        deadline_dt.strftime("%Y-%m-%d %H:%M")
                        if deadline_dt
                        else "No deadline specified"
                    )
                    org = (
                        item.get("organisation", {}).get("name")
                        if isinstance(item.get("organisation"), dict)
                        else (item.get("organisation") or "Partner")
                    )
                    title_clean = title[:65].encode("ascii", "ignore").decode("ascii")
                    org_clean = str(org)[:30].encode("ascii", "ignore").decode("ascii")
                    print(f"  [ACTIVE/UPCOMING] [{org_clean}] {title_clean}")
                    print(f"                    Deadline: {dl_str}")

                print(
                    f"\n--> Active/Upcoming in {opp_type}: {valid_count} / {len(raw_items)}"
                )

    print("\n============================================================")
    print(f"TOTAL ACTIVE & UPCOMING OPPORTUNITIES FOUND: {total_valid}")
    print("============================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
