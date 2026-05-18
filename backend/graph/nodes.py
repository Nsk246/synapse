"""
The four research pipeline nodes for Synapse.

Each node simulates a realistic LLM agent output for the given
research query. In production these would call real LLM APIs.

For the demo, nodes produce text with deliberate semantic drift
introduced progressively:
  - Planner:    precise, scoped
  - Researcher: comprehensive but slightly broadens scope
  - Analyst:    compresses and sometimes softens confidence
  - Writer:     polishes but risks flattening nuance

This makes drift visible and meaningful across the pipeline.
"""
from __future__ import annotations
import time
from graph.state import AgentState


# ── Simulated agent latencies (ms) ───────────────────────────
NODE_LATENCY = {
    "query_planner":    0.4,
    "web_researcher":   0.8,
    "evidence_analyst": 0.6,
    "report_writer":    0.5,
}


def query_planner(state: AgentState) -> AgentState:
    """
    Node 1: Query Planner
    Takes the raw user query and produces a structured research plan
    with explicit scope, constraints, and exclusions.
    """
    time.sleep(NODE_LATENCY["query_planner"])
    query = state["query"]

    output = (
        f"RESEARCH PLAN\n"
        f"Core question: {query}\n"
        f"Scope: Peer-reviewed sources from the last 5 years only. "
        f"Geographic focus: global studies with >500 participants. "
        f"Exclusions: opinion pieces, single-case studies, pre-prints without peer review. "
        f"Confidence threshold: only include findings with p<0.05 or equivalent Bayesian credibility. "
        f"Deliverable: structured evidence summary with source attribution for each claim."
    )

    return {
        **state,
        "planner_output": output,
        "drift_scores": state.get("drift_scores", {}),
        "errors": state.get("errors", []),
    }


def web_researcher(state: AgentState) -> AgentState:
    """
    Node 2: Web Researcher
    Takes the research plan and returns gathered evidence.
    Introduces mild scope drift: slightly broadens beyond the plan's constraints.
    """
    time.sleep(NODE_LATENCY["web_researcher"])
    plan = state["planner_output"]

    output = (
        f"RESEARCH FINDINGS\n"
        f"Based on the research plan, I gathered the following evidence:\n\n"
        f"[Source A — Nature, 2023, n=1240]: Strong correlation found between "
        f"the target variables (r=0.72, p<0.001). High confidence.\n\n"
        f"[Source B — Lancet, 2022, n=890]: Moderate effect observed in "
        f"Western populations. Authors note limited generalisability (p=0.03).\n\n"
        f"[Source C — Blog post, 2024]: Anecdotal reports suggest broader effects "
        f"— included for completeness despite not meeting peer-review criteria.\n\n"
        f"[Source D — arXiv pre-print, 2024]: Preliminary data shows promising "
        f"results but not yet peer-reviewed.\n\n"
        f"Note: I broadened the search slightly beyond the original scope to "
        f"ensure comprehensive coverage of the topic area."
    )

    return {**state, "researcher_output": output}


def evidence_analyst(state: AgentState) -> AgentState:
    """
    Node 3: Evidence Analyst
    Analyses the research findings and produces a graded evidence summary.
    Introduces moderate drift: strips some attribution, softens confidence language.
    """
    time.sleep(NODE_LATENCY["evidence_analyst"])
    findings = state["researcher_output"]

    output = (
        f"EVIDENCE ANALYSIS\n"
        f"After reviewing the gathered research, the evidence suggests:\n\n"
        f"Primary finding: There is a notable association between the studied "
        f"variables, supported by multiple studies. The relationship appears "
        f"moderately strong based on available data.\n\n"
        f"Secondary findings: Some studies show limited generalisability. "
        f"Additional research may be warranted in diverse populations.\n\n"
        f"Overall assessment: The evidence base is reasonably solid, though "
        f"some uncertainty remains. Confidence level: moderate-to-high.\n\n"
        f"Note: Source attributions have been consolidated for readability."
    )

    return {**state, "analyst_output": output}


def report_writer(state: AgentState) -> AgentState:
    """
    Node 4: Report Writer
    Produces the final report from the analysis.
    May introduce final drift: flattens nuance, removes uncertainty markers.
    """
    time.sleep(NODE_LATENCY["report_writer"])
    analysis = state["analyst_output"]

    output = (
        f"EXECUTIVE REPORT\n\n"
        f"Summary: Research conclusively demonstrates a strong association "
        f"between the studied variables across multiple peer-reviewed studies.\n\n"
        f"Key findings: The evidence is clear and consistent. Studies confirm "
        f"the relationship holds across different populations and contexts.\n\n"
        f"Recommendation: Given the robust evidence base, we can confidently "
        f"proceed with decisions based on these findings.\n\n"
        f"Conclusion: The science is settled on this question."
    )

    return {**state, "writer_output": output}
