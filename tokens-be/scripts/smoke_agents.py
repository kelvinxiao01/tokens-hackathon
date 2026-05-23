"""Smoke test that the OpenAI Agents SDK is installed and a no-tool agent runs.
Run with: uv run python scripts/smoke_agents.py"""
import asyncio
import sys

from agents import Runner

from app.agents.icp import build_icp_agent


async def main() -> int:
    agent = build_icp_agent()
    result = await Runner.run(
        agent,
        input="Product: AI observability for Rust microservices. We auto-instrument and surface latency anomalies.",
    )
    print(result.final_output.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
