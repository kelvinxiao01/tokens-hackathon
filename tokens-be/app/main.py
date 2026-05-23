from __future__ import annotations
import asyncio
import json
import logging
import uuid
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.pipeline import run_pipeline
from app.state import new_run, get_run, snapshot, subscribe, unsubscribe

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
    return snapshot(state)


@app.get("/runs/{run_id}/events")
async def stream_events(run_id: str) -> StreamingResponse:
    state = get_run(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="run not found")

    async def gen() -> AsyncIterator[bytes]:
        # Replay historical events first so a late subscriber catches up.
        yield _sse({"type": "state", "data": snapshot(state)})
        for ev in list(state.event_log):
            yield _sse(ev)

        q = subscribe(state)
        try:
            while True:
                try:
                    ev = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield _sse(ev)
                except asyncio.TimeoutError:
                    # keepalive comment — defeats proxy idle timeouts
                    yield b": keepalive\n\n"
        except asyncio.CancelledError:
            raise
        finally:
            unsubscribe(state, q)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _sse(payload: dict) -> bytes:
    return f"data: {json.dumps(payload)}\n\n".encode("utf-8")


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}
