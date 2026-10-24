"""
app/graph/workflow.py — LangGraph StateGraph definition.

Topology:
  START → analyze_query → retrieve → evaluate_evidence
                                            ↓          ↓
                                    [sufficient] [insufficient]
                                         ↓              ↓
                                   generate_answer   fallback
                                         ↓              ↓
                                        END            END
"""

from __future__ import annotations

import logging
import time
from typing import Any

from langgraph.graph import StateGraph, START, END

from app.graph.state import RAGState
from app.graph.nodes import (
    analyze_query,
    retrieve,
    evaluate_evidence,
    generate_answer,
    fallback,
)

logger = logging.getLogger(__name__)


def _route_evidence(state: RAGState) -> str:
    """Conditional edge: route to generate or fallback based on evidence."""
    if state.get("evidence_sufficient", False):
        return "generate_answer"
    return "fallback"


def build_workflow() -> Any:
    """Build and compile the LangGraph RAG workflow."""
    graph = StateGraph(RAGState)

    # Register nodes
    graph.add_node("analyze_query", analyze_query)
    graph.add_node("retrieve", retrieve)
    graph.add_node("evaluate_evidence", evaluate_evidence)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("fallback", fallback)

    # Edges
    graph.add_edge(START, "analyze_query")
    graph.add_edge("analyze_query", "retrieve")
    graph.add_edge("retrieve", "evaluate_evidence")

    # Conditional: evidence sufficient?
    graph.add_conditional_edges(
        "evaluate_evidence",
        _route_evidence,
        {
            "generate_answer": "generate_answer",
            "fallback": "fallback",
        },
    )

    graph.add_edge("generate_answer", END)
    graph.add_edge("fallback", END)

    compiled = graph.compile()
    logger.info("LangGraph RAG workflow compiled.")
    return compiled


class RAGWorkflow:
    """
    High-level wrapper around the compiled LangGraph workflow.
    Handles timing and error containment.
    """

    def __init__(self) -> None:
        self._graph = build_workflow()

    def run(
        self,
        query: str,
        language: str = "auto",
        session_id: str | None = None,
    ) -> RAGState:
        """Execute the full RAG pipeline and return the final state."""
        t0 = time.perf_counter()

        initial_state: RAGState = {
            "query": query,
            "language": language,
            "session_id": session_id,
        }

        try:
            final_state = self._graph.invoke(initial_state)
        except Exception as exc:
            logger.error("Workflow error: %s", exc, exc_info=True)
            from app.generation.prompts import FALLBACK_ENGLISH
            final_state = dict(initial_state)
            final_state.update(
                {
                    "answer": FALLBACK_ENGLISH,
                    "citations": [],
                    "limitations": ["An internal error occurred."],
                    "status": "error",
                    "error": str(exc),
                    "response_language": "en",
                }
            )

        elapsed_ms = (time.perf_counter() - t0) * 1000
        final_state["latency_ms"] = round(elapsed_ms, 1)

        logger.info(
            "Workflow complete — status: %s, latency: %.0f ms",
            final_state.get("status"), elapsed_ms,
        )
        return final_state  # type: ignore[return-value]

