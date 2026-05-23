from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from app.models import ICP, ProspectCandidate, ProspectDossier, CallBrief


@dataclass
class ProspectResult:
    candidate: ProspectCandidate
    status: str = "queued"  # queued | research | ingest | analyze | brief | done | error
    dossier: Optional[ProspectDossier] = None
    brief: Optional[CallBrief] = None
    senso_content_ids: list[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class RunState:
    run_id: str
    product: str
    step: str = "queued"
    icp: Optional[ICP] = None
    candidates: list[ProspectCandidate] = field(default_factory=list)
    prospects: list[ProspectResult] = field(default_factory=list)
    error: Optional[str] = None

    subscribers: list[asyncio.Queue] = field(default_factory=list)
    event_log: list[dict] = field(default_factory=list)


RUNS: dict[str, RunState] = {}


def new_run(run_id: str, product: str) -> RunState:
    state = RunState(run_id=run_id, product=product)
    RUNS[run_id] = state
    return state


def get_run(run_id: str) -> Optional[RunState]:
    return RUNS.get(run_id)


def snapshot(state: RunState) -> dict:
    return {
        "run_id": state.run_id,
        "product": state.product,
        "step": state.step,
        "error": state.error,
        "icp": state.icp.model_dump() if state.icp else None,
        "prospects": [
            {
                "candidate": p.candidate.model_dump(),
                "status": p.status,
                "dossier": p.dossier.model_dump() if p.dossier else None,
                "brief": p.brief.model_dump() if p.brief else None,
                "senso_content_ids": p.senso_content_ids,
                "error": p.error,
            }
            for p in state.prospects
        ],
    }


def _publish(state: RunState, event: dict) -> None:
    state.event_log.append(event)
    if len(state.event_log) > 500:
        state.event_log = state.event_log[-500:]
    for q in list(state.subscribers):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            pass


def publish_state(state: RunState) -> None:
    _publish(state, {"type": "state", "ts": time.time(), "data": snapshot(state)})


def publish_log(
    state: RunState,
    message: str,
    *,
    level: str = "info",
    agent: Optional[str] = None,
    prospect: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> None:
    _publish(
        state,
        {
            "type": "log",
            "ts": time.time(),
            "level": level,
            "agent": agent,
            "prospect": prospect,
            "message": message,
            "meta": meta or {},
        },
    )


def subscribe(state: RunState) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=1000)
    state.subscribers.append(q)
    return q


def unsubscribe(state: RunState, q: asyncio.Queue) -> None:
    if q in state.subscribers:
        state.subscribers.remove(q)
