import json
from dataclasses import dataclass

from agents import function_tool, RunContextWrapper

from app.clients import senso_client


@dataclass
class ProspectKBContext:
    """Per-prospect context — pinned to the analyst/brief agents so they query the right KB."""
    category_id: str
    prospect_name: str


@function_tool
async def senso_query(
    wrapper: RunContextWrapper[ProspectKBContext],
    question: str,
) -> str:
    """Query the prospect's grounded knowledge base. Use for every factual claim you make."""
    try:
        out = await senso_client.query(
            question=question,
            category_id=wrapper.context.category_id,
        )
    except Exception as e:
        return f"ERROR: {e}"
    return json.dumps(out)[:8000]
