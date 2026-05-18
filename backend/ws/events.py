"""
Synapse WebSocket event emitters.

One function per event type. Each constructs the typed payload
and calls manager.broadcast(). All 9 event types are covered:

  node_start       — node begins execution
  node_complete    — node finished, carries duration + preview
  handoff_start    — edge begins transmitting
  schema_pass      — Phase 1 cleared
  schema_fail      — Phase 1 blocked
  drift_pass       — Phase 2 cleared, carries cosine score
  drift_fail       — Phase 2 blocked, carries score + diff data
  override         — human accepted a drift failure
  run_complete     — full pipeline finished
"""
from __future__ import annotations
import time
from ws.hub import manager


def _ts() -> int:
    return int(time.time() * 1000)


async def emit_node_start(node_id: str) -> None:
    await manager.broadcast({
        "type":      "node_start",
        "timestamp": _ts(),
        "nodeId":    node_id,
    })


async def emit_node_complete(
    node_id: str,
    duration_ms: float,
    output_preview: str,
) -> None:
    await manager.broadcast({
        "type":           "node_complete",
        "timestamp":      _ts(),
        "nodeId":         node_id,
        "duration_ms":    duration_ms,
        "output_preview": output_preview[:200],
    })


async def emit_handoff_start(
    edge_id: str,
    from_node: str,
    to_node: str,
) -> None:
    await manager.broadcast({
        "type":      "handoff_start",
        "timestamp": _ts(),
        "edgeId":    edge_id,
        "fromNode":  from_node,
        "toNode":    to_node,
    })


async def emit_schema_pass(edge_id: str, schema_name: str) -> None:
    await manager.broadcast({
        "type":        "schema_pass",
        "timestamp":   _ts(),
        "edgeId":      edge_id,
        "schema_name": schema_name,
    })


async def emit_schema_fail(edge_id: str, error: str) -> None:
    await manager.broadcast({
        "type":      "schema_fail",
        "timestamp": _ts(),
        "edgeId":    edge_id,
        "error":     error,
    })


async def emit_drift_pass(
    edge_id: str,
    score: float,
    threshold: float,
) -> None:
    await manager.broadcast({
        "type":      "drift_pass",
        "timestamp": _ts(),
        "edgeId":    edge_id,
        "score":     score,
        "threshold": threshold,
    })


async def emit_drift_fail(
    edge_id: str,
    score: float,
    threshold: float,
    original_intent: str,
    transformed_output: str,
) -> None:
    await manager.broadcast({
        "type":               "drift_fail",
        "timestamp":          _ts(),
        "edgeId":             edge_id,
        "score":              score,
        "threshold":          threshold,
        "original_intent":    original_intent,
        "transformed_output": transformed_output[:400],
    })


async def emit_override(edge_id: str, reason: str) -> None:
    await manager.broadcast({
        "type":      "override",
        "timestamp": _ts(),
        "edgeId":    edge_id,
        "reason":    reason,
    })


async def emit_run_complete(
    total_duration_ms: float,
    drift_events: int,
) -> None:
    await manager.broadcast({
        "type":              "run_complete",
        "timestamp":         _ts(),
        "total_duration_ms": total_duration_ms,
        "drift_events":      drift_events,
    })
