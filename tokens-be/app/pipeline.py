from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional, TypeVar

from agents import Runner
from pydantic import BaseModel

from app.agents.icp import build_icp_agent
from app.agents.discovery import build_discovery_agent
from app.agents.researcher import build_researcher_agent
from app.agents.analyst import build_analyst_agent
from app.agents.brief import build_brief_agent
from app.clients import senso_client
from app.config import PROSPECTS_PER_RUN, SENSO_INDEX_WAIT_SECONDS
from app.models import ICP, ResearchOutput
from app.state import RunState, ProspectResult, publish_state, publish_log
from app.tools.senso import ProspectKBContext

log = logging.getLogger("sdr.pipeline")

T = TypeVar("T", bound=BaseModel)


async def _run_agent_streamed(
    state: RunState,
    agent,
    input: str,
    *,
    context: Optional[Any] = None,
    max_turns: int = 20,
    prospect: Optional[str] = None,
):
    """Run an agent with streaming and pipe SDK events into the run's event bus."""
    kwargs: dict[str, Any] = {"input": input, "max_turns": max_turns}
    if context is not None:
        kwargs["context"] = context
    result = Runner.run_streamed(agent, **kwargs)

    async for event in result.stream_events():
        et = event.type
        if et == "raw_response_event":
            continue
        if et == "agent_updated_stream_event":
            publish_log(
                state,
                f"agent → {event.new_agent.name}",
                agent=event.new_agent.name,
                prospect=prospect,
            )
            continue
        if et == "run_item_stream_event":
            item = event.item
            it = item.type
            if it == "tool_call_item":
                tool_name = getattr(item.raw_item, "name", "tool")
                args_preview = ""
                raw_args = getattr(item.raw_item, "arguments", None)
                if isinstance(raw_args, str):
                    args_preview = raw_args[:140]
                publish_log(
                    state,
                    f"tool · {tool_name}({args_preview})",
                    agent=agent.name,
                    prospect=prospect,
                    meta={"tool": tool_name},
                )
            elif it == "tool_call_output_item":
                out_preview = str(item.output)[:120].replace("\n", " ")
                publish_log(
                    state,
                    f"tool → {out_preview}",
                    agent=agent.name,
                    prospect=prospect,
                )
            elif it == "message_output_item":
                # final message; usually the structured output is filled.
                pass
    return result.final_output


async def run_pipeline(state: RunState) -> None:
    publish_log(state, f"run started: {state.product[:80]}")
    publish_state(state)
    try:
        state.step = "icp"
        publish_log(state, "step: extract ICP", agent="ICP Agent")
        publish_state(state)
        icp: ICP = await _run_agent_streamed(
            state, build_icp_agent(), f"Product: {state.product}", max_turns=4
        )
        state.icp = icp
        publish_log(state, f"ICP: {', '.join(icp.industries[:3]) or '—'}", agent="ICP Agent")
        publish_state(state)

        state.step = "discovery"
        publish_log(state, "step: discover prospects", agent="Discovery Agent")
        publish_state(state)
        disc_input = (
            f"ICP:\n{icp.model_dump_json(indent=2)}\n\n"
            f"Find up to {PROSPECTS_PER_RUN} candidate companies using the search queries."
        )
        disc_out = await _run_agent_streamed(
            state, build_discovery_agent(), disc_input, max_turns=20
        )
        candidates = disc_out.candidates[:PROSPECTS_PER_RUN]
        state.candidates = candidates
        state.prospects = [ProspectResult(candidate=c) for c in candidates]
        publish_log(state, f"discovered {len(candidates)} prospects")
        publish_state(state)

        for pr in state.prospects:
            try:
                await _process_prospect(state, pr, icp)
            except Exception as e:
                log.exception("prospect %s failed", pr.candidate.name)
                pr.status = "error"
                pr.error = str(e)
                publish_log(state, f"prospect failed: {e}", level="error", prospect=pr.candidate.name)
                publish_state(state)

        state.step = "done"
        publish_log(state, "run complete")
        publish_state(state)
    except Exception as e:
        log.exception("pipeline failed")
        state.step = "error"
        state.error = str(e)
        publish_log(state, f"pipeline error: {e}", level="error")
        publish_state(state)


async def _process_prospect(state: RunState, pr: ProspectResult, icp: ICP) -> None:
    name = pr.candidate.name

    pr.status = "research"
    state.step = f"research:{name}"
    publish_log(state, f"researching {name}", agent="Researcher Agent", prospect=name)
    publish_state(state)
    r_input = (
        f"Prospect: {name}\nHomepage: {pr.candidate.homepage_url}\n"
        f"One-liner: {pr.candidate.one_liner}\n\nResearch this company."
    )
    research: ResearchOutput = await _run_agent_streamed(
        state, build_researcher_agent(), r_input, max_turns=30, prospect=name
    )
    publish_log(state, f"scraped {len(research.docs)} docs", prospect=name)

    pr.status = "ingest"
    state.step = f"ingest:{name}"
    publish_log(state, "ingesting into Senso KB", prospect=name)
    publish_state(state)
    content_ids: list[str] = []
    skipped = 0
    for doc in research.docs:
        title = f"[{state.run_id}] {name} · {doc.title or doc.url}"[:200]
        try:
            cid = await senso_client.ingest_raw(title=title, text=doc.content)
            content_ids.append(cid)
        except senso_client.SensoDuplicateContent:
            skipped += 1
    pr.senso_content_ids = content_ids
    publish_log(
        state,
        f"ingested {len(content_ids)} docs" + (f" (skipped {skipped} dupes)" if skipped else ""),
        prospect=name,
    )
    if SENSO_INDEX_WAIT_SECONDS > 0 and content_ids:
        publish_log(state, f"waiting {SENSO_INDEX_WAIT_SECONDS}s for Senso indexing", prospect=name)
        await asyncio.sleep(SENSO_INDEX_WAIT_SECONDS)

    ctx = ProspectKBContext(prospect_name=name, content_ids=content_ids)

    pr.status = "analyze"
    state.step = f"analyze:{name}"
    publish_log(state, "analyzing", agent="Analyst Agent", prospect=name)
    publish_state(state)
    a_input = (
        f"Prospect: {name} ({pr.candidate.homepage_url})\n\n"
        f"Seller ICP:\n{icp.model_dump_json(indent=2)}\n\nBuild the dossier."
    )
    pr.dossier = await _run_agent_streamed(
        state, build_analyst_agent(), a_input, context=ctx, max_turns=20, prospect=name
    )
    publish_log(state, f"dossier ready (fit {pr.dossier.fit_score}/10)", prospect=name)
    publish_state(state)

    pr.status = "brief"
    state.step = f"brief:{name}"
    publish_log(state, "writing call brief", agent="Brief Writer Agent", prospect=name)
    publish_state(state)
    b_input = (
        f"Prospect: {name}\n\nSeller product:\n{state.product}\n\n"
        f"Dossier:\n{pr.dossier.model_dump_json(indent=2)}\n\nWrite the call brief."
    )
    pr.brief = await _run_agent_streamed(
        state, build_brief_agent(), b_input, context=ctx, max_turns=15, prospect=name
    )
    pr.status = "done"
    publish_log(state, "brief ready", prospect=name)
    publish_state(state)
