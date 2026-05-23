"""Smoke test the Senso client end-to-end. Run with:
   PYTHONPATH=. uv run python scripts/smoke_senso.py"""
import asyncio
import json
import sys

from app.clients import senso_client
from app.config import SENSO_INDEX_WAIT_SECONDS


async def main() -> int:
    print("=== whoami ===")
    me = await senso_client.whoami()
    print(f"org_id={me.get('org_id')}, name={me.get('name')}, tier_free={me.get('is_free_tier')}")

    import time
    stamp = int(time.time())
    print("\n=== ingest_raw ===")
    cid = await senso_client.ingest_raw(
        title=f"smoke {stamp} · Acme Corp homepage",
        text=(
            f"[smoke {stamp}] Acme Corp sells industrial widgets to Series B+ "
            "manufacturing companies. Their head of sales is Jane Doe. CTO is John Smith."
        ),
    )
    print("content_id:", cid)

    wait = max(SENSO_INDEX_WAIT_SECONDS, 5)
    print(f"\n--- waiting {wait}s for indexing ---")
    await asyncio.sleep(wait)

    print("\n=== search (scoped) ===")
    out = await senso_client.search(
        query="Who is the head of sales at Acme?",
        content_ids=[cid],
        max_results=3,
    )
    print(json.dumps(out, indent=2)[:1800])
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
