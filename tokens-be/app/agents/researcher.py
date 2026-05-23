from agents import Agent

from app.config import RESEARCH_MODEL
from app.models import ResearchOutput
from app.tools.nimble import nimble_search, nimble_extract, nimble_map


INSTRUCTIONS = """You build a research corpus on a single prospect company.

You will receive a candidate's name and homepage URL.

Process:
1. Call nimble_map on the homepage to see what pages exist.
2. Pick the 4-6 most informative pages (homepage, about, product/pricing, team/leadership, blog index, careers). Skip legal, login, status pages.
3. Call nimble_extract on each to pull markdown.
4. Run 1-2 nimble_search queries for recent signals: e.g. "<company> funding 2025", "<company> hiring".
5. For each piece of content you gather, capture: url, a short title, and the markdown content (trim heavy boilerplate but keep facts).

Goal: a tight, fact-dense corpus another agent can ingest into a knowledge base. Aim for 5-8 docs total. Do not summarize across docs — return them raw.

Return the structured ResearchOutput object."""


def build_researcher_agent() -> Agent:
    return Agent(
        name="Researcher Agent",
        instructions=INSTRUCTIONS,
        model=RESEARCH_MODEL,
        tools=[nimble_map, nimble_extract, nimble_search],
        output_type=ResearchOutput,
    )
