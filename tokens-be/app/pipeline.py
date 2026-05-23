from __future__ import annotations
import logging

from agents import Runner

from app.agents.icp import build_icp_agent
from app.agents.discovery import build_discovery_agent
from app.agents.researcher import build_researcher_agent
from app.agents.analyst import build_analyst_agent
from app.agents.brief import build_brief_agent
from app.clients import senso_client
from app.config import PROSPECTS_PER_RUN
from app.models import ICP, CandidateList, ResearchOutput, ProspectDossier, CallBrief
from app.state import RunState, ProspectResult
from app.tools.senso import ProspectKBContext

log = logging.getLogger("sdr.pipeline")


async def run_pipeline(state: RunState) -> None:
    try:
        state.step = "icp"
        icp_agent = build_icp_agent()
        icp_res = await Runner.run(icp_agent, input=f"Product: {state.product}")
        icp: ICP = icp_res.final_output
        state.icp = icp
        log.info("ICP done: %s", icp.model_dump_json())

        state.step = "discovery"
        discovery_agent = build_discovery_agent()
        disc_input = (
            f"ICP:\n{icp.model_dump_json(indent=2)}\n\n"
            f"Find up to {PROSPECTS_PER_RUN} candidate companies using the search queries."
        )
        disc_res = await Runner.run(discovery_agent, input=disc_input, max_turns=20)
        candidates: list = disc_res.final_output.candidates[:PROSPECTS_PER_RUN]
        state.candidates = candidates
        state.prospects = [ProspectResult(candidate=c) for c in candidates]
        log.info("Discovery done: %d candidates", len(candidates))

        for pr in state.prospects:
            try:
                await _process_prospect(state, pr, icp)
            except Exception as e:
                log.exception("prospect %s failed", pr.candidate.name)
                pr.error = str(e)

        state.step = "done"
    except Exception as e:
        log.exception("pipeline failed")
        state.step = "error"
        state.error = str(e)


async def _process_prospect(state: RunState, pr: ProspectResult, icp: ICP) -> None:
    name = pr.candidate.name

    state.step = f"research:{name}"
    researcher_agent = build_researcher_agent()
    r_input = (
        f"Prospect: {name}\nHomepage: {pr.candidate.homepage_url}\n"
        f"One-liner: {pr.candidate.one_liner}\n\nResearch this company."
    )
    r_res = await Runner.run(researcher_agent, input=r_input, max_turns=30)
    research: ResearchOutput = r_res.final_output
    log.info("research done %s: %d docs", name, len(research.docs))

    state.step = f"ingest:{name}"
    category_id = await senso_client.create_category(f"prospect:{name}")
    pr.senso_category_id = category_id
    for doc in research.docs:
        await senso_client.ingest_raw(
            title=doc.title or doc.url,
            content=doc.content,
            category_id=category_id,
        )

    ctx = ProspectKBContext(category_id=category_id, prospect_name=name)

    state.step = f"analyze:{name}"
    analyst_agent = build_analyst_agent()
    a_input = (
        f"Prospect: {name} ({pr.candidate.homepage_url})\n\n"
        f"Seller ICP:\n{icp.model_dump_json(indent=2)}\n\n"
        f"Build the dossier."
    )
    a_res = await Runner.run(analyst_agent, input=a_input, context=ctx, max_turns=20)
    pr.dossier = a_res.final_output

    state.step = f"brief:{name}"
    brief_agent = build_brief_agent()
    b_input = (
        f"Prospect: {name}\n\nSeller product:\n{state.product}\n\n"
        f"Dossier:\n{pr.dossier.model_dump_json(indent=2)}\n\nWrite the call brief."
    )
    b_res = await Runner.run(brief_agent, input=b_input, context=ctx, max_turns=15)
    pr.brief = b_res.final_output
    log.info("brief done %s", name)
