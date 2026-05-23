from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from app.models import ICP, ProspectCandidate, ProspectDossier, CallBrief


@dataclass
class ProspectResult:
    candidate: ProspectCandidate
    dossier: Optional[ProspectDossier] = None
    brief: Optional[CallBrief] = None
    senso_category_id: Optional[str] = None
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


RUNS: dict[str, RunState] = {}


def new_run(run_id: str, product: str) -> RunState:
    state = RunState(run_id=run_id, product=product)
    RUNS[run_id] = state
    return state


def get_run(run_id: str) -> Optional[RunState]:
    return RUNS.get(run_id)
