from typing import Any
import httpx

from app.config import SENSO_API_KEY, SENSO_BASE_URL


# NOTE: Senso's public API reference is sign-in-walled at https://docs.senso.ai/reference.
# Base URL and auth header confirmed from https://docs.senso.ai/docs/authentication
# (X-API-Key, base https://apiv2.senso.ai/api/v1). Endpoint *paths* below are
# best-guess against the documented "ingest, query, generate" surface and should
# be verified the first time the smoke script is run against a real key.
INGEST_PATH = "/content/raw"
QUERY_PATH = "/query"
CATEGORY_PATH = "/categories"


class SensoError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    if not SENSO_API_KEY:
        raise SensoError("SENSO_API_KEY not set")
    return {
        "X-API-Key": SENSO_API_KEY,
        "Content-Type": "application/json",
    }


async def _post(path: str, body: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as c:
        r = await c.post(f"{SENSO_BASE_URL}{path}", headers=_headers(), json=body)
        if r.status_code >= 400:
            raise SensoError(f"Senso {path} {r.status_code}: {r.text[:500]}")
        return r.json()


async def create_category(name: str) -> str:
    """Create a per-prospect category (KB scope). Returns the category id."""
    out = await _post(CATEGORY_PATH, {"name": name})
    cat_id = out.get("id") or out.get("category_id") or out.get("data", {}).get("id")
    if not cat_id:
        raise SensoError(f"create_category: no id in response: {out}")
    return str(cat_id)


async def ingest_raw(title: str, content: str, category_id: str | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"title": title, "content": content}
    if category_id:
        body["category_id"] = category_id
    return await _post(INGEST_PATH, body)


async def query(question: str, category_id: str | None = None, limit: int = 5) -> dict[str, Any]:
    body: dict[str, Any] = {"query": question, "limit": limit}
    if category_id:
        body["category_id"] = category_id
    return await _post(QUERY_PATH, body)
