"""
Phase 2 — Semantic Drift Validator.

Computes cosine similarity between:
  A = embedding of the SynapseContract.intent (what must be preserved)
  B = embedding of the validated HandoffPayload.content (what was output)

Cosine similarity formula:
  S_C(A, B) = (A · B) / (||A||_2 * ||B||_2)

If S_C < threshold (τ, default 0.85), semantic drift is detected
and the handoff is blocked.

Model: sentence-transformers/all-MiniLM-L6-v2
  - 384-dimensional dense vector space
  - ~22.7M parameters, ~80MB
  - L2-normalised output → dot product = cosine similarity
"""
from __future__ import annotations
import os
import numpy as np
from functools import lru_cache
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer


# ── Model singleton (loaded once, reused across all requests) ─
@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load all-MiniLM-L6-v2 once and cache it in memory."""
    print("▸ Loading all-MiniLM-L6-v2 (first call only)...")
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def _embed(text: str) -> np.ndarray:
    """Encode text into a 384-d L2-normalised vector."""
    model = _get_model()
    return model.encode(text, normalize_embeddings=True)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    S_C(A, B) = (A · B) / (||A||_2 * ||B||_2)
    Since both vectors are L2-normalised by the encoder,
    this reduces to a simple dot product.
    """
    return float(np.dot(a, b))


class DriftResult(BaseModel):
    passed: bool
    score: float
    threshold: float
    intent: str
    output_preview: str
    error: str | None = None


def run_semantic_drift(
    intent: str,
    output: str,
    threshold: float | None = None,
) -> DriftResult:
    """
    Validate that 'output' semantically preserves 'intent'.

    Args:
        intent:    The SynapseContract.intent string.
        output:    The agent's validated output content.
        threshold: τ override. Falls back to SEMANTIC_THRESHOLD env var,
                   then to 0.85.

    Returns:
        DriftResult with passed=True if S_C >= τ, else passed=False.
    """
    if threshold is None:
        threshold = float(os.getenv("SEMANTIC_THRESHOLD", "0.85"))

    try:
        vec_a = _embed(intent)
        vec_b = _embed(output)
        score = cosine_similarity(vec_a, vec_b)

        return DriftResult(
            passed=score >= threshold,
            score=round(score, 4),
            threshold=threshold,
            intent=intent,
            output_preview=output[:200],
        )

    except Exception as e:
        return DriftResult(
            passed=False,
            score=0.0,
            threshold=threshold,
            intent=intent,
            output_preview=output[:200],
            error=f"Embedding error: {str(e)}",
        )
