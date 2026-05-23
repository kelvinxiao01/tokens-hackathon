import json
from dataclasses import dataclass, field

from agents import function_tool, RunContextWrapper

from app.clients import senso_client


@dataclass
class ProspectKBContext:
    """Per-prospect context — pinned to the analyst/brief agents so their queries
    are scoped to that prospect's docs in the shared org KB."""
    prospect_name: str
    content_ids: list[str] = field(default_factory=list)


@function_tool
async def senso_query(
    wrapper: RunContextWrapper[ProspectKBContext],
    question: str,
) -> str:
    """Query the prospect's grounded knowledge base. Use for every factual claim you make."""
    ctx = wrapper.context
    try:
        out = await senso_client.search(
            query=question,
            content_ids=ctx.content_ids,
            max_results=5,
        )
    except Exception as e:
        return f"ERROR: {e}"
    return json.dumps(out)[:8000]
