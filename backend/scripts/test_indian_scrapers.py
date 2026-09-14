import asyncio

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}


async def test():
    async with httpx.AsyncClient(
        timeout=15.0, follow_redirects=True, headers=HEADERS, verify=False
    ) as client:
        # 1. IIT Delhi IRD Vacancies
        try:
            r = await client.get("https://ird.iitd.ac.in/vacancies")
            print("IIT Delhi IRD status:", r.status_code)
            soup = BeautifulSoup(r.text, "html.parser")
            rows = soup.find_all("tr")
            print(f"IIT Delhi Table Rows: {len(rows)}")
            for row in rows[:10]:
                text = row.get_text(strip=True)
                if any(
                    k in text.lower()
                    for k in ["research", "project", "assistant", "fellow", "intern"]
                ):
                    print("  IIT Delhi Row:", text[:120])
        except Exception as e:
            print("IIT Delhi error:", e)

        # 2. IISc Bangalore News & Fellowships
        try:
            r = await client.get("https://iisc.ac.in/events/")
            print("IISc Events status:", r.status_code)
            soup = BeautifulSoup(r.text, "html.parser")
            titles = [
                a.get_text(strip=True)
                for a in soup.find_all("a")
                if len(a.get_text(strip=True)) > 10
            ]
            print(f"IISc Titles found: {len(titles)}")
            for t in titles[:5]:
                print("  IISc Title:", t)
        except Exception as e:
            print("IISc error:", e)

        # 3. DRDO Careers & Internships
        try:
            r = await client.get("https://www.drdo.gov.in/drdo/careers")
            print("DRDO Careers status:", r.status_code)
            soup = BeautifulSoup(r.text, "html.parser")
            items = [
                a.get_text(strip=True)
                for a in soup.find_all("a")
                if "intern" in a.get_text(strip=True).lower()
                or "jrf" in a.get_text(strip=True).lower()
                or "research" in a.get_text(strip=True).lower()
            ]
            print(f"DRDO Items: {len(items)}")
            for item in items[:5]:
                print("  DRDO Item:", item)
        except Exception as e:
            print("DRDO error:", e)


if __name__ == "__main__":
    asyncio.run(test())
