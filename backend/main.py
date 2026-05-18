"""
Synapse — FastAPI application entry point.

Endpoints:
  GET  /health      — liveness check
  POST /api/run     — execute the research pipeline with validation
  GET  /api/schema  — return the three handoff contracts as JSON

The /api/run endpoint executes the LangGraph pipeline step-by-step,
running both validation phases at each handoff boundary.
WebSocket streaming is added in Milestone 3.
"""
from __future__ import annotations
import os
import time
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.contracts import CONTRACTS
from core.schema_gate import run_schema_gate
from core.semantic_drift import run_semantic_drift
from graph.state import AgentState
from graph.nodes import query_planner, web_researcher, evidence_analyst, report_writer

load_dotenv()

app = FastAPI(
    title="Synapse",
    description="Real-time semantic observability for multi-agent LLM pipelines",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.app.github.dev"],
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


# ── Validation middleware ─────────────────────────────────────
def validate_handoff(
    from_node: str,
    to_node: str,
    output: str,
    threshold: float,
) -> HandoffResult:
    """
    Run both validation phases for a single handoff.
    Returns a HandoffResult capturing the outcome of each phase.
    """
    edge_id = f"{from_node}_to_{to_node}"
    contract = CONTRACTS.get(edge_id)

    if not contract:
        return HandoffResult(
            edge_id=edge_id,
            from_node=from_node,
            to_node=to_node,
            schema_passed=False,
            error=f"No contract registered for edge '{edge_id}'",
        )

    # Phase 1: Schema Gate
    schema_result = run_schema_gate(output)
    if not schema_result.passed:
        return HandoffResult(
            edge_id=edge_id,
            from_node=from_node,
            to_node=to_node,
            schema_passed=False,
            error=schema_result.error,
        )

    # Phase 2: Semantic Drift
    drift_result = run_semantic_drift(
        intent=contract.intent,
        output=schema_result.payload.content,
        threshold=threshold,
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


# ── Endpoints ─────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "synapse", "version": "0.1.0"}


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
    Execute the full research pipeline with validation at every handoff.

    Steps:
      1. Run query_planner
      2. Validate planner → researcher handoff
      3. Run web_researcher
      4. Validate researcher → analyst handoff
      5. Run evidence_analyst
      6. Validate analyst → writer handoff
      7. Run report_writer
    """
    run_id = str(uuid.uuid4())[:8]
    start  = time.time()
    handoffs: list[HandoffResult] = []

    # Initialise state
    state: AgentState = {
        "query":             request.query,
        "planner_output":    "",
        "researcher_output": "",
        "analyst_output":    "",
        "writer_output":     "",
        "drift_scores":      {},
        "errors":            [],
        "threshold":         request.threshold,
        "metadata":          {"run_id": run_id},
    }

    try:
        # ── Node 1: Query Planner ─────────────────────────────
        state = query_planner(state)

        # ── Handoff 1: Planner → Researcher ──────────────────
        h1 = validate_handoff(
            "query_planner", "web_researcher",
            state["planner_output"], request.threshold,
        )
        handoffs.append(h1)
        if h1.drift_score is not None:
            state["drift_scores"]["planner_to_researcher"] = h1.drift_score

        # ── Node 2: Web Researcher ────────────────────────────
        state = web_researcher(state)

        # ── Handoff 2: Researcher → Analyst ──────────────────
        h2 = validate_handoff(
            "web_researcher", "evidence_analyst",
            state["researcher_output"], request.threshold,
        )
        handoffs.append(h2)
        if h2.drift_score is not None:
            state["drift_scores"]["researcher_to_analyst"] = h2.drift_score

        # ── Node 3: Evidence Analyst ──────────────────────────
        state = evidence_analyst(state)

        # ── Handoff 3: Analyst → Writer ───────────────────────
        h3 = validate_handoff(
            "evidence_analyst", "report_writer",
            state["analyst_output"], request.threshold,
        )
        handoffs.append(h3)
        if h3.drift_score is not None:
            state["drift_scores"]["analyst_to_writer"] = h3.drift_score

        # ── Node 4: Report Writer ─────────────────────────────
        state = report_writer(state)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    duration     = round((time.time() - start) * 1000, 1)
    drift_events = sum(1 for h in handoffs if h.drift_passed is False)
    overall      = "drift_detected" if drift_events > 0 else "complete"

    return RunResponse(
        run_id=run_id,
        query=request.query,
        status=overall,
        total_duration_ms=duration,
        handoffs=handoffs,
        final_output=state["writer_output"],
        drift_event_count=drift_events,
    )
