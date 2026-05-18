"""
LangGraph shared state for the Synapse research pipeline.
Passed through every node; each node reads and writes its slice.
"""
from __future__ import annotations
from typing import TypedDict, Any


class AgentState(TypedDict):
    # Original user query
    query: str

    # Per-node outputs (populated as the graph runs)
    planner_output: str
    researcher_output: str
    analyst_output: str
    writer_output: str

    # Drift scores recorded at each handoff
    drift_scores: dict[str, float]

    # Any validation errors encountered
    errors: list[str]

    # Runtime threshold (can be overridden per-run)
    threshold: float

    # Arbitrary metadata bag
    metadata: dict[str, Any]
