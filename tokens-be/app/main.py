from __future__ import annotations
import asyncio
import logging
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.pipeline import run_pipeline
from app.state import new_run, get_run

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Autonomous SDR")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateRunBody(BaseModel):
    product: str


@app.post("/runs")
async def create_run(body: CreateRunBody) -> dict:
    run_id = uuid.uuid4().hex[:12]
    state = new_run(run_id, body.product)
    asyncio.create_task(run_pipeline(state))
    return {"run_id": run_id}


@app.get("/runs/{run_id}")
async def read_run(run_id: str) -> dict:
    state = get_run(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "run_id": state.run_id,
        "product": state.product,
        "step": state.step,
        "error": state.error,
        "icp": state.icp.model_dump() if state.icp else None,
        "prospects": [
            {
                "candidate": p.candidate.model_dump(),
                "dossier": p.dossier.model_dump() if p.dossier else None,
                "brief": p.brief.model_dump() if p.brief else None,
                "senso_category_id": p.senso_category_id,
                "error": p.error,
            }
            for p in state.prospects
        ],
    }


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}
