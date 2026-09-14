import asyncio
import sys

import httpx

sys.path.insert(0, ".")
from app.core.redis import cache_delete_pattern, close_redis, init_redis


async def main():
    try:
        await init_redis()
        await cache_delete_pattern("*")
        print("[REDIS] Successfully flushed all Redis cache keys!")
        await close_redis()
    except Exception as e:
        print(f"[REDIS] Redis flush note: {e}")

    async with httpx.AsyncClient() as http:
        res = await http.get("http://localhost:8000/api/v1/feed?limit=60")
        data = res.json()
        items = data.get("items", [])
        print(f"\n[API] Feed endpoint returned {len(items)} items:")
        for idx, item in enumerate(items, 1):
            title = item["title"][:70].encode("ascii", "ignore").decode("ascii")
            inst = (
                (item.get("institution") or "Unknown")
                .encode("ascii", "ignore")
                .decode("ascii")
            )
            print(f"  {idx}. [{inst}] {title}")


if __name__ == "__main__":
    asyncio.run(main())
