"""
app/graph/state.py — LangGraph state schema for the RAG workflow.

TypedDict fields carry data between graph nodes.
All fields are Optional so each node only reads what it needs.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict


class RAGState(TypedDict, total=False):
    # ---- Input ----
    query: str                          # Original user query
    language: str                       # Requested language: 'bn' | 'en' | 'auto'
    session_id: Optional[str]

    # ---- Analysis ----
    detected_language: str              # Actual detected language of the query
    response_language: str             # Language to use for the answer
    normalized_query: str              # Cleaned/normalized query for retrieval
    query_intent: str                  # 'procedure' | 'document' | 'fee' | 'general'
    query_category: str                # 'passport' | 'nid' | 'tin' | 'general'

    # ---- Retrieval ----
    bm25_results: list[tuple[Any, float]]          # [(DocumentChunk, score)]
    dense_results: list[tuple[dict, float]]        # [(metadata_dict, similarity)]
    fused_candidates: list[tuple[str, dict, float]]  # [(chunk_id, meta, rrf_score)]
    reranked_passages: list[tuple[str, dict, float]] # [(chunk_id, meta, reranker_score)]

    # ---- Evidence evaluation ----
    evidence_sufficient: bool
    evidence_score: float              # Composite score [0,1]
    evidence_notes: list[str]         # Flags, conflicts, freshness warnings

    # ---- Generation ----
    answer: str
    citations: list[dict]             # Serialised CitationModel-like dicts
    limitations: list[str]

    # ---- Output ----
    status: str                       # ResponseStatus value
    error: Optional[str]              # Internal error message (not sent to user)
    latency_ms: Optional[float]

