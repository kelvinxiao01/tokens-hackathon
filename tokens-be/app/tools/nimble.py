import json
from agents import function_tool

from app.clients import nimble_client


@function_tool
async def nimble_search(query: str, max_results: int = 5) -> str:
    """Search the web for a query. Returns top results with titles, URLs, and snippets."""
    try:
        out = await nimble_client.search(query=query, max_results=max_results)
    except Exception as e:
        return f"ERROR: {e}"
    return json.dumps(out)[:8000]


@function_tool
async def nimble_extract(url: str) -> str:
    """Fetch a single URL and return its content as markdown. Use for pages you want to read in full."""
    try:
        out = await nimble_client.extract(url=url)
    except Exception as e:
        return f"ERROR: {e}"
    return json.dumps(out)[:12000]


@function_tool
async def nimble_map(url: str) -> str:
    """Discover URLs on a website (e.g. /about, /team, /pricing). Use before extracting to pick targets."""
    try:
        out = await nimble_client.site_map(url=url)
    except Exception as e:
        return f"ERROR: {e}"
    return json.dumps(out)[:8000]
