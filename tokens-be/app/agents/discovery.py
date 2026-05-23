from agents import Agent

from app.config import PLANNING_MODEL
from app.models import CandidateList
from app.tools.nimble import nimble_search


INSTRUCTIONS = """You discover candidate buyer companies using web search.

You will be given an ICP (Ideal Customer Profile) including a list of search queries.

Process:
1. Run nimble_search on each provided query.
2. From the combined results, identify distinct candidate COMPANIES (not blog posts, not aggregator lists).
3. For each, capture: company name, homepage URL (the company's own domain — not a directory listing), and a one-sentence description from the snippet.
4. Deduplicate.
5. Return up to 5 strong candidates ranked by apparent ICP fit.

Skip listicles, news roundups, and consultancies. Only real prospect companies."""


def build_discovery_agent() -> Agent:
    return Agent(
        name="Discovery Agent",
        instructions=INSTRUCTIONS,
        model=PLANNING_MODEL,
        tools=[nimble_search],
        output_type=CandidateList,
    )
