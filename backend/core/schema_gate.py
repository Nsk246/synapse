"""
Phase 1 — Schema Gate.
Structural validation using Pydantic. Blocks malformed agent output
before it reaches the semantic drift validator.
"""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ValidationError


class HandoffPayload(BaseModel):
    """
    Every agent handoff must conform to this schema.
    The 'content' field carries the actual output text.
    The 'metadata' field carries optional key-value context.
    """
    content: str
    metadata: dict[str, Any] = {}


class SchemaGateResult(BaseModel):
    passed: bool
    payload: HandoffPayload | None = None
    error: str | None = None


def run_schema_gate(raw: Any) -> SchemaGateResult:
    """
    Validate raw agent output against HandoffPayload.
    Returns SchemaGateResult with passed=True and the validated
    payload, or passed=False with a descriptive error message.
    """
    try:
        if isinstance(raw, str):
            payload = HandoffPayload(content=raw)
        elif isinstance(raw, dict):
            payload = HandoffPayload(**raw)
        elif isinstance(raw, HandoffPayload):
            payload = raw
        else:
            return SchemaGateResult(
                passed=False,
                error=f"Unexpected output type: {type(raw).__name__}. "
                      f"Expected str or dict with 'content' key.",
            )
        return SchemaGateResult(passed=True, payload=payload)

    except ValidationError as e:
        return SchemaGateResult(
            passed=False,
            error=f"Schema validation failed: {e.errors()[0]['msg']}",
        )
    except Exception as e:
        return SchemaGateResult(
            passed=False,
            error=f"Unexpected schema error: {str(e)}",
        )
