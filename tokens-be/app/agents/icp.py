from agents import Agent

from app.config import PLANNING_MODEL
from app.models import ICP


INSTRUCTIONS = """You translate a product/service description into an Ideal Customer Profile (ICP).

Given a short product blurb, infer:
- which industries/verticals this serves
- what company size/stage typically buys it
- which decision-maker roles to target
- observable signals (in news, job posts, tech stack, hiring) that indicate a company has the pain this product solves
- 3-5 concrete web search queries that would surface candidate buyer companies

Be specific. "B2B SaaS companies" is too broad — prefer "Series A-C developer-tools companies with 20-150 engineers shipping production services."

The search queries should be the kind a human SDR would type into Google. Examples:
- "Series B fintech companies hiring head of compliance 2025"
- "open source vector database companies series A"
- "logistics startups 50-200 employees New York"

Return only the structured ICP object."""


def build_icp_agent() -> Agent:
    return Agent(
        name="ICP Agent",
        instructions=INSTRUCTIONS,
        model=PLANNING_MODEL,
        output_type=ICP,
    )
