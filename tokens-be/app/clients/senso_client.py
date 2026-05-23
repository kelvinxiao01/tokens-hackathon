"""Senso REST client.

Endpoints + request shapes confirmed by inspecting the official @senso-ai/cli
bundle and live-probing the API. The key implies the org — every path is
under /org/... with no org_id in the URL.

Per-prospect isolation: the search endpoint scopes by `content_ids`, so we
ingest each prospect's docs, collect the returned ids, and pass them on every
search. (Documents can also carry tag_ids, but search filters by content_id.)
"""
from typing import Any
import httpx

from app.config import SENSO_API_KEY, SENSO_BASE_URL


class SensoError(RuntimeError):
    pass


class SensoDuplicateContent(SensoError):
    """Raised on HTTP 409 — Senso de-dupes by content hash; the existing doc id
    is not returned, so callers should either ignore or vary the content/title."""


def _headers() -> dict[str, str]:
    if not SENSO_API_KEY:
        raise SensoError("SENSO_API_KEY not set")
    return {
        "x-api-key": SENSO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def _request(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as c:
        r = await c.request(method, f"{SENSO_BASE_URL}{path}", headers=_headers(), json=body)
        if r.status_code == 409:
            raise SensoDuplicateContent(f"Senso {method} {path} 409: {r.text[:300]}")
        if r.status_code >= 400:
            raise SensoError(f"Senso {method} {path} {r.status_code}: {r.text[:500]}")
        return r.json() if r.content else {}


async def whoami() -> dict[str, Any]:
    return await _request("GET", "/org/me")


async def ingest_raw(title: str, text: str, tag_ids: list[str] | None = None) -> str:
    """Ingest a raw markdown/text document. Returns the new content id.

    Processing is async (HTTP 202): the doc is queued and becomes searchable
    after Senso finishes embedding it (usually seconds).
    """
    body: dict[str, Any] = {"title": title or "untitled", "text": text}
    if tag_ids:
        body["tag_ids"] = tag_ids
    out = await _request("POST", "/org/kb/raw", body)
    content_id = out.get("id") or out.get("content_id")
    if not content_id:
        raise SensoError(f"ingest_raw: no id in response: {out}")
    return str(content_id)


async def search(
    query: str,
    *,
    content_ids: list[str] | None = None,
    max_results: int = 5,
    require_scoped_ids: bool = True,
) -> dict[str, Any]:
    """Search the org KB. When content_ids is given, restrict results to those docs."""
    body: dict[str, Any] = {"query": query, "max_results": max_results}
    if content_ids:
        body["content_ids"] = content_ids
        body["require_scoped_ids"] = require_scoped_ids
    return await _request("POST", "/org/search", body)
