"""
Synapse — FastAPI application with WebSocket streaming.

Endpoints:
  GET  /health        — liveness check
  GET  /api/schema    — handoff contracts as JSON
  POST /api/run       — execute pipeline (REST, returns full result)
  POST /api/run/stream — execute pipeline, stream events via WS
  WS   /ws/trace      — WebSocket endpoint for live event stream
  POST /api/override  — accept a drift failure and log the decision
"""
from __future__ import annotations
import os
import time
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.contracts import CONTRACTS
from core.schema_gate import run_schema_gate
from core.semantic_drift import run_semantic_drift
from graph.state import AgentState
from graph.nodes import (
    query_planner,
    web_researcher,
    evidence_analyst,
    report_writer,
)
from ws.hub import manager
from ws.events import (
    emit_node_start,
    emit_node_complete,
    emit_handoff_start,
    emit_schema_pass,
    emit_schema_fail,
    emit_drift_pass,
    emit_drift_fail,
    emit_run_complete,
)

load_dotenv()

app = FastAPI(
    title="Synapse",
    description="Real-time semantic observability for multi-agent LLM pipelines",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────
class RunRequest(BaseModel):
    query: str
    threshold: float = float(os.getenv("SEMANTIC_THRESHOLD", "0.85"))


class HandoffResult(BaseModel):
    edge_id: str
    from_node: str
    to_node: str
    schema_passed: bool
    drift_passed: bool | None = None
    drift_score: float | None = None
    threshold: float | None = None
    error: str | None = None


class RunResponse(BaseModel):
    run_id: str
    query: str
    status: str
    total_duration_ms: float
    handoffs: list[HandoffResult]
    final_output: str | None = None
    drift_event_count: int


class OverrideRequest(BaseModel):
    edge_id: str
    reason: str = "Manually accepted by operator"


# ── Core validation logic (used by both REST and streaming) ───
async def validate_handoff_streaming(
    from_node: str,
    to_node: str,
    output: str,
    threshold: float,
) -> HandoffResult:
    """
    Run both validation phases and emit WebSocket events at each step.
    """
    edge_id  = f"{from_node}_to_{to_node}"
    contract = CONTRACTS.get(edge_id)

    await emit_handoff_start(edge_id, from_node, to_node)

    if not contract:
        err = f"No contract registered for edge '{edge_id}'"
        await emit_schema_fail(edge_id, err)
        return HandoffResult(
            edge_id=edge_id,
            from_node=from_node,
            to_node=to_node,
            schema_passed=False,
            error=err,
        )

    # Phase 1: Schema Gate
    schema_result = run_schema_gate(output)
    if not schema_result.passed:
        await emit_schema_fail(edge_id, schema_result.error or "Schema failed")
        return HandoffResult(
            edge_id=edge_id,
            from_node=from_node,
            to_node=to_node,
            schema_passed=False,
            error=schema_result.error,
        )

    await emit_schema_pass(edge_id, "HandoffPayload")

    # Phase 2: Semantic Drift
    drift_result = run_semantic_drift(
        intent=contract.intent,
        output=schema_result.payload.content,
        threshold=threshold,
    )

    if drift_result.passed:
        await emit_drift_pass(edge_id, drift_result.score, drift_result.threshold)
    else:
        await emit_drift_fail(
            edge_id=edge_id,
            score=drift_result.score,
            threshold=drift_result.threshold,
            original_intent=contract.intent,
            transformed_output=schema_result.payload.content,
        )

    return HandoffResult(
        edge_id=edge_id,
        from_node=from_node,
        to_node=to_node,
        schema_passed=True,
        drift_passed=drift_result.passed,
        drift_score=drift_result.score,
        threshold=drift_result.threshold,
        error=drift_result.error,
    )


# ── Pipeline executor (streaming-aware) ──────────────────────
async def execute_pipeline(
    query: str,
    threshold: float,
    run_id: str,
) -> RunResponse:
    """
    Execute all 4 nodes, emitting WebSocket events at every step.
    """
    start    = time.time()
    handoffs: list[HandoffResult] = []

    state: AgentState = {
        "query":             query,
        "planner_output":    "",
        "researcher_output": "",
        "analyst_output":    "",
        "writer_output":     "",
        "drift_scores":      {},
        "errors":            [],
        "threshold":         threshold,
        "metadata":          {"run_id": run_id},
    }

    # ── Node 1: Query Planner ─────────────────────────────────
    t0 = time.time()
    await emit_node_start("query_planner")
    state = query_planner(state)
    await emit_node_complete(
        "query_planner",
        round((time.time() - t0) * 1000, 1),
        state["planner_output"],
    )

    # ── Handoff 1 ─────────────────────────────────────────────
    h1 = await validate_handoff_streaming(
        "query_planner", "web_researcher",
        state["planner_output"], threshold,
    )
    handoffs.append(h1)
    if h1.drift_score is not None:
        state["drift_scores"]["query_planner_to_web_researcher"] = h1.drift_score

    # ── Node 2: Web Researcher ────────────────────────────────
    t0 = time.time()
    await emit_node_start("web_researcher")
    state = web_researcher(state)
    await emit_node_complete(
        "web_researcher",
        round((time.time() - t0) * 1000, 1),
        state["researcher_output"],
    )

    # ── Handoff 2 ─────────────────────────────────────────────
    h2 = await validate_handoff_streaming(
        "web_researcher", "evidence_analyst",
        state["researcher_output"], threshold,
    )
    handoffs.append(h2)
    if h2.drift_score is not None:
        state["drift_scores"]["web_researcher_to_evidence_analyst"] = h2.drift_score

    # ── Node 3: Evidence Analyst ──────────────────────────────
    t0 = time.time()
    await emit_node_start("evidence_analyst")
    state = evidence_analyst(state)
    await emit_node_complete(
        "evidence_analyst",
        round((time.time() - t0) * 1000, 1),
        state["analyst_output"],
    )

    # ── Handoff 3 ─────────────────────────────────────────────
    h3 = await validate_handoff_streaming(
        "evidence_analyst", "report_writer",
        state["analyst_output"], threshold,
    )
    handoffs.append(h3)
    if h3.drift_score is not None:
        state["drift_scores"]["evidence_analyst_to_report_writer"] = h3.drift_score

    # ── Node 4: Report Writer ─────────────────────────────────
    t0 = time.time()
    await emit_node_start("report_writer")
    state = report_writer(state)
    await emit_node_complete(
        "report_writer",
        round((time.time() - t0) * 1000, 1),
        state["writer_output"],
    )

    duration     = round((time.time() - start) * 1000, 1)
    drift_events = sum(1 for h in handoffs if h.drift_passed is False)
    await emit_run_complete(duration, drift_events)

    return RunResponse(
        run_id=run_id,
        query=query,
        status="drift_detected" if drift_events > 0 else "complete",
        total_duration_ms=duration,
        handoffs=handoffs,
        final_output=state["writer_output"],
        drift_event_count=drift_events,
    )


# ── WebSocket endpoint ────────────────────────────────────────
@app.websocket("/ws/trace")
async def websocket_trace(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Keep connection alive; client sends pings
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ── REST endpoints ────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status":      "ok",
        "service":     "synapse",
        "version":     "0.2.0",
        "ws_clients":  len(manager.active),
    }


@app.get("/api/schema")
async def get_contracts():
    return {
        edge_id: {
            "edge_id":     c.edge_id,
            "from_node":   c.from_node,
            "to_node":     c.to_node,
            "intent":      c.intent,
            "description": c.description,
        }
        for edge_id, c in CONTRACTS.items()
    }


@app.post("/api/run", response_model=RunResponse)
async def run_pipeline(request: RunRequest):
    """
    Execute the pipeline. Streams events to all connected
    WebSocket clients in real-time while returning the full
    result as a REST response.
    """
    run_id = str(uuid.uuid4())[:8]
    try:
        return await execute_pipeline(request.query, request.threshold, run_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/override")
async def override_drift(request: OverrideRequest):
    """
    Accept a drift failure and allow the pipeline to continue.
    Logs the human decision and broadcasts the override event.
    """
    from ws.events import emit_override
    await emit_override(request.edge_id, request.reason)
    return {
        "accepted": True,
        "edge_id":  request.edge_id,
        "reason":   request.reason,
    }
