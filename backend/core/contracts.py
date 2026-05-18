"""
SynapseContract: a declared semantic intent for each agent handoff.
The drift validator checks cosine similarity against this contract's
intent string — not just the raw previous output.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SynapseContract:
    edge_id: str
    from_node: str
    to_node: str
    intent: str          # what must be semantically preserved
    description: str     # human-readable explanation


# ── The three handoff contracts for the Research Pipeline ────

CONTRACTS: dict[str, SynapseContract] = {
    "planner_to_researcher": SynapseContract(
        edge_id="planner_to_researcher",
        from_node="query_planner",
        to_node="web_researcher",
        intent=(
            "Preserve the core research question, its scope constraints, "
            "and any explicit exclusions specified by the user."
        ),
        description="Planner → Researcher: research question + constraints must survive",
    ),
    "researcher_to_analyst": SynapseContract(
        edge_id="researcher_to_analyst",
        from_node="web_researcher",
        to_node="evidence_analyst",
        intent=(
            "Preserve all factual claims with their source attributions, "
            "confidence levels, and contradicting evidence intact."
        ),
        description="Researcher → Analyst: facts + attribution must not be stripped",
    ),
    "analyst_to_writer": SynapseContract(
        edge_id="analyst_to_writer",
        from_node="evidence_analyst",
        to_node="report_writer",
        intent=(
            "Preserve severity qualifiers, confidence ratings, and uncertainty "
            "markers — do not flatten nuance for readability."
        ),
        description="Analyst → Writer: severity/confidence qualifiers must survive",
    ),
}
