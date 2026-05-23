from typing import Any
import httpx

from app.config import NIMBLE_API_KEY, NIMBLE_BASE_URL


class NimbleError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    if not NIMBLE_API_KEY:
        raise NimbleError("NIMBLE_API_KEY not set")
    return {
        "Authorization": f"Bearer {NIMBLE_API_KEY}",
        "Content-Type": "application/json",
    }


async def _post(path: str, body: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as c:
        r = await c.post(f"{NIMBLE_BASE_URL}{path}", headers=_headers(), json=body)
        if r.status_code >= 400:
            raise NimbleError(f"Nimble {path} {r.status_code}: {r.text[:500]}")
        return r.json()


async def search(query: str, max_results: int = 5, depth: str = "lite") -> dict[str, Any]:
    return await _post("/search", {
        "query": query,
        "max_results": max_results,
        "search_depth": depth,
        "include_answer": False,
    })


async def extract(url: str, formats: list[str] | None = None) -> dict[str, Any]:
    return await _post("/extract", {
        "url": url,
        "formats": formats or ["markdown"],
        "render": True,
    })


async def site_map(url: str) -> dict[str, Any]:
    return await _post("/map", {
        "url": url,
        "sitemap": "include",
    })
