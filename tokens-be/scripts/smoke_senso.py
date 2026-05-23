"""Smoke test the Senso client. Run with: uv run python scripts/smoke_senso.py

If this fails with 404s, the guessed endpoint paths in app/clients/senso_client.py
(INGEST_PATH / QUERY_PATH / CATEGORY_PATH) need to be corrected against the live
API reference at https://docs.senso.ai/reference (sign-in required)."""
import asyncio
import json
import sys

from app.clients import senso_client


async def main() -> int:
    print("=== create_category ===")
    cat_id = await senso_client.create_category("smoke-test")
    print("category_id:", cat_id)

    print("\n=== ingest_raw ===")
    out = await senso_client.ingest_raw(
        title="Acme Corp homepage",
        content="Acme Corp sells industrial widgets to Series B+ manufacturing companies. Their head of sales is Jane Doe.",
        category_id=cat_id,
    )
    print(json.dumps(out, indent=2)[:1500])

    print("\n=== query ===")
    out = await senso_client.query(
        question="Who is the head of sales at Acme?",
        category_id=cat_id,
    )
    print(json.dumps(out, indent=2)[:1500])

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
