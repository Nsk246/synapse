"""
LangGraph StateGraph builder for the Synapse research pipeline.

The graph wires the four nodes together. Semantic validation
is performed by the middleware layer in main.py before each
node transition — the graph itself stays clean and composable.

Graph structure:
  START → query_planner → web_researcher → evidence_analyst → report_writer → END
"""
from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from graph.state import AgentState
from graph.nodes import (
    query_planner,
    web_researcher,
    evidence_analyst,
    report_writer,
)


def build_graph() -> StateGraph:
    """
    Compile and return the Synapse research pipeline StateGraph.
    """
    builder = StateGraph(AgentState)

    # Register nodes
    builder.add_node("query_planner",    query_planner)
    builder.add_node("web_researcher",   web_researcher)
    builder.add_node("evidence_analyst", evidence_analyst)
    builder.add_node("report_writer",    report_writer)

    # Wire edges
    builder.add_edge(START,              "query_planner")
    builder.add_edge("query_planner",    "web_researcher")
    builder.add_edge("web_researcher",   "evidence_analyst")
    builder.add_edge("evidence_analyst", "report_writer")
    builder.add_edge("report_writer",    END)

    return builder.compile()


# Module-level compiled graph (imported by main.py)
graph = build_graph()
