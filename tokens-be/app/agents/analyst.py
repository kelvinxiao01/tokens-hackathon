from agents import Agent

from app.config import PLANNING_MODEL
from app.models import ProspectDossier
from app.tools.senso import senso_query, ProspectKBContext


INSTRUCTIONS = """You produce a grounded dossier for one prospect company.

You have one tool: senso_query, which searches the prospect's knowledge base (built from scraped pages about that company). Every factual claim in your dossier MUST be supported by a senso_query result. Cite source URLs returned by the tool.

You will be given the prospect name + URL and the seller's ICP (what pains they look for).

Process (call senso_query repeatedly):
1. "What does this company do? What products do they sell?" → fills what_they_do
2. "Who runs sales/engineering/operations? Names and titles." → decision_makers
3. For each pain_signal in the ICP, query specifically for evidence (e.g. "Is the company hiring for X?", "Have they mentioned scaling problems?") → pain_signals_found
4. Score fit 0-10 based on signal density vs ICP. Be honest — a 3 is fine if the evidence is weak.
5. Capture the source URLs you cited as `citations`.

Do NOT invent facts. If the KB doesn't support a claim, omit it."""


def build_analyst_agent() -> Agent[ProspectKBContext]:
    return Agent[ProspectKBContext](
        name="Analyst Agent",
        instructions=INSTRUCTIONS,
        model=PLANNING_MODEL,
        tools=[senso_query],
        output_type=ProspectDossier,
    )
