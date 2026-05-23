"""Smoke test the Nimbleway client. Run with: uv run python scripts/smoke_nimble.py"""
import asyncio
import json
import sys

from app.clients import nimble_client


async def main() -> int:
    print("=== nimble_search ===")
    out = await nimble_client.search("OpenAI Agents SDK", max_results=3)
    print(json.dumps(out, indent=2)[:1500])

    print("\n=== nimble_map ===")
    out = await nimble_client.site_map("https://docs.nimbleway.com")
    print(json.dumps(out, indent=2)[:1500])

    print("\n=== nimble_extract ===")
    out = await nimble_client.extract("https://docs.nimbleway.com/home")
    print(json.dumps(out, indent=2)[:1500])

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
