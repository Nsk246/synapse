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
    intent: str
    description: str


# Keys match the edge_id format used in main.py:
# f"{from_node}_to_{to_node}"

CONTRACTS: dict[str, SynapseContract] = {
    "query_planner_to_web_researcher": SynapseContract(
        edge_id="query_planner_to_web_researcher",
        from_node="query_planner",
        to_node="web_researcher",
        intent=(
            "Preserve the core research question, its scope constraints, "
            "and any explicit exclusions specified by the user."
        ),
        description="Planner → Researcher: research question + constraints must survive",
    ),
    "web_researcher_to_evidence_analyst": SynapseContract(
        edge_id="web_researcher_to_evidence_analyst",
        from_node="web_researcher",
        to_node="evidence_analyst",
        intent=(
            "Preserve all factual claims with their source attributions, "
            "confidence levels, and contradicting evidence intact."
        ),
        description="Researcher → Analyst: facts + attribution must not be stripped",
    ),
    "evidence_analyst_to_report_writer": SynapseContract(
        edge_id="evidence_analyst_to_report_writer",
        from_node="evidence_analyst",
        to_node="report_writer",
        intent=(
            "Preserve severity qualifiers, confidence ratings, and uncertainty "
            "markers — do not flatten nuance for readability."
        ),
        description="Analyst → Writer: severity/confidence qualifiers must survive",
    ),
}
