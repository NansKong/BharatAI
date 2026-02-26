"""
URL Health-Checker: Validates all MonitoredSource URLs in the DB and
marks broken ones as inactive (failure_count >= 10).

Run:
  docker exec -it bharatai-backend-1 python -m scripts.check_urls

Options:
  DRY_RUN=1 python -m scripts.check_urls   # report only, don't mutate
"""
import asyncio
import os
import sys
import time

import httpx

sys.path.insert(0, ".")
from app.core.database import AsyncSessionLocal, close_database, init_database
from app.models.opportunity import MonitoredSource
from sqlalchemy import select

DRY_RUN = os.getenv("DRY_RUN", "0") == "1"
TIMEOUT = 12  # seconds
CONCURRENCY = 20  # parallel requests
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (BharatAI URL Checker/1.0; "
        "+https://github.com/bharatai) AppleWebKit/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

OK_CODES = {200, 201, 202, 203, 204, 206, 301, 302, 303, 307, 308}
SKIP_CODES = {403, 429}  # auth/rate-limit — don't mark broken

# Keywords that indicate an SSL issue worth retrying without verification
_SSL_KEYWORDS = ("ssl", "certificate", "dh key", "handshake", "verify")


def _is_ssl_err(msg: str) -> bool:
    m = msg.lower()
    return any(k in m for k in _SSL_KEYWORDS)


async def _ssl_retry(url: str) -> tuple[bool, int]:
    """Retry with verify=False for sites with self-signed / weak certs."""
    try:
        async with httpx.AsyncClient(verify=False, timeout=TIMEOUT) as c:
            r = await c.head(url, headers=HEADERS, follow_redirects=True)
            if r.status_code in SKIP_CODES:
                r = await c.get(url, headers=HEADERS, follow_redirects=True)
            return (
                r.status_code in OK_CODES or r.status_code in SKIP_CODES
            ), r.status_code
    except Exception:
        return False, 0


async def check_url(client: httpx.AsyncClient, url: str) -> tuple[bool, int, str]:
    """Returns (is_ok, status_code, error_msg)."""
    try:
        r = await client.head(
            url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True
        )
        if r.status_code in SKIP_CODES:
            r = await client.get(
                url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True
            )
        ok = r.status_code in OK_CODES or r.status_code in SKIP_CODES
        return ok, r.status_code, ""
    except httpx.ConnectError as e:
        err = str(e)
        if _is_ssl_err(err):
            ok, code = await _ssl_retry(url)
            if ok:
                return True, code, "ssl_unverified"
        return False, 0, err[:120]
    except httpx.TimeoutException:
        return False, 0, "timeout"
    except httpx.TooManyRedirects:
        return False, 0, "too_many_redirects"
    except Exception as e:
        err = str(e)
        # Catch SSL errors that surface as generic exceptions (e.g. CERTIFICATE_VERIFY_FAILED)
        if _is_ssl_err(err):
            ok, code = await _ssl_retry(url)
            if ok:
                return True, code, "ssl_unverified"
        return False, 0, err[:120]


async def run():
    await init_database()
    async with AsyncSessionLocal() as db:
        sources = (await db.execute(select(MonitoredSource))).scalars().all()
    await close_database()

    print(f"\n🔍 Checking {len(sources)} source URLs  (DRY_RUN={DRY_RUN})\n{'─'*60}")

    sem = asyncio.Semaphore(CONCURRENCY)
    results = {"ok": [], "broken": [], "skipped": []}

    async def bounded_check(source):
        async with sem:
            async with httpx.AsyncClient() as client:
                ok, code, err = await check_url(client, source.url)
            return source, ok, code, err

    tasks = [bounded_check(s) for s in sources]
    checked = 0
    broken_sources = []

    for coro in asyncio.as_completed(tasks):
        source, ok, code, err = await coro
        checked += 1
        pct = checked / len(sources) * 100

        if ok:
            results["ok"].append(source.url)
            status = f"✅ {code}"
        elif code in SKIP_CODES:
            results["skipped"].append(source.url)
            status = f"⚠️  {code} (auth/rate-limit, skipped)"
        else:
            results["broken"].append(source.url)
            broken_sources.append((source, code, err))
            status = f"❌ {code or 'ERR'} — {err}"

        print(f"  [{pct:5.1f}%] {source.name[:40]:<40} {status}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"  ✅ OK      : {len(results['ok'])}")
    print(f"  ⚠️  Skipped : {len(results['skipped'])}")
    print(f"  ❌ Broken  : {len(results['broken'])}")

    if broken_sources:
        print(f"\n{'─'*60}")
        print("BROKEN SOURCES:")
        for s, code, err in broken_sources:
            print(f"  • {s.name}: {s.url}")
            print(f"    → {code or 'no response'} {err}")

    # ── Deactivate broken sources ─────────────────────────────────────────────
    if not DRY_RUN and broken_sources:
        await init_database()
        async with AsyncSessionLocal() as db:
            deactivated = 0
            for source, code, err in broken_sources:
                # Reload fresh from DB
                s = (
                    await db.execute(
                        select(MonitoredSource).where(MonitoredSource.id == source.id)
                    )
                ).scalar_one_or_none()
                if s:
                    s.failure_count = max(s.failure_count + 1, 10)
                    s.last_error = f"URL check: HTTP {code} – {err}"[:500]
                    if s.failure_count >= 10:
                        s.active = False
                        deactivated += 1
            await db.commit()
        await close_database()
        print(f"\n🗑  Deactivated {deactivated} chronically broken sources.")
    elif DRY_RUN:
        print("\n  [DRY RUN — no DB changes made]")

    print("\nDone.")


if __name__ == "__main__":
    t0 = time.monotonic()
    asyncio.run(run())
    print(f"  Elapsed: {time.monotonic() - t0:.1f}s")
