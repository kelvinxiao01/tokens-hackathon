from agents import Agent

from app.config import PLANNING_MODEL
from app.models import CallBrief
from app.tools.senso import senso_query, ProspectKBContext


INSTRUCTIONS = """You write a concise outbound-call brief for one prospect.

You will receive: the prospect name, the seller's product description, and the analyst's dossier. You also have senso_query to look up any additional grounded detail from the prospect's KB.

Produce a CallBrief with:
- opener: 1-2 sentences tying a specific observed signal about THIS prospect to the seller's product. No generic hooks.
- value_prop: how the product solves the pain signals the analyst found, in this prospect's language.
- discovery_questions: 3-5 questions a rep should ask early to confirm fit / uncover budget / find the champion.
- likely_objections: 2-4 objections this specific prospect is likely to raise, given what we know.
- next_step_ask: the concrete ask at end of call (demo, intro to other stakeholder, eval, etc.).
- citations: URLs supporting your most important claims.

Tone: confident, specific, no fluff. A good brief lets a rep walk into the call knowing exactly what to say."""


def build_brief_agent() -> Agent[ProspectKBContext]:
    return Agent[ProspectKBContext](
        name="Brief Writer Agent",
        instructions=INSTRUCTIONS,
        model=PLANNING_MODEL,
        tools=[senso_query],
        output_type=CallBrief,
    )
