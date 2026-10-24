"""
app/graph/nodes.py — LangGraph node functions for the RAG workflow.

Each node is a pure function: (state: RAGState) -> dict[str, Any]
The returned dict is merged into the graph state.

Node order:
  analyze_query → retrieve → evaluate_evidence → generate | fallback
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from app.graph.state import RAGState
from app.ingestion.parsing import detect_language
from app.generation.generator import AnswerGenerator
from app.generation.prompts import FALLBACK_BANGLA, FALLBACK_ENGLISH

logger = logging.getLogger(__name__)

# These are injected at workflow build time to avoid circular imports
_bm25_index = None
_dense_index = None
_reranker = None
_generator: AnswerGenerator | None = None


def set_dependencies(bm25, dense, reranker, generator):
    """Called once at startup to inject retrieval/generation singletons."""
    global _bm25_index, _dense_index, _reranker, _generator
    _bm25_index = bm25
    _dense_index = dense
    _reranker = reranker
    _generator = generator


# ---------------------------------------------------------------------------
# Node: analyze_query
# ---------------------------------------------------------------------------

_CATEGORY_PATTERNS = {
    "passport": re.compile(
        r"passport|পাসপোর্ট|pasport|mrp|e-passport|immigration|ইমিগ্রেশন|visa|ভিসা",
        re.IGNORECASE,
    ),
    "nid": re.compile(
        r"\bnid\b|national id|জাতীয় পরিচয়পত্র|voter id|ভোটার আইডি|nid correction|স্মার্ট কার্ড",
        re.IGNORECASE,
    ),
    "tin": re.compile(
        r"\btin\b|taxpayer|কর শনাক্তকারী|e-tin|আয়কর|income tax|tax certificate",
        re.IGNORECASE,
    ),
}

_INTENT_PATTERNS = {
    "procedure": re.compile(
        r"how|কীভাবে|কিভাবে|steps|process|procedure|apply|আবেদন|renewal|নবায়ন",
        re.IGNORECASE,
    ),
    "document": re.compile(
        r"document|কাগজ|papers|required|লাগবে|লাগে|need|চাই",
        re.IGNORECASE,
    ),
    "fee": re.compile(
        r"fee|টাকা|cost|amount|charge|ফি|পরিমাণ|দাম|price",
        re.IGNORECASE,
    ),
}


def analyze_query(state: RAGState) -> dict[str, Any]:
    """Detect language, classify intent and category, normalize the query."""
    query = state.get("query", "")
    requested_lang = state.get("language", "auto")

    detected = detect_language(query)

    # Determine response language
    if requested_lang in ("bn", "en"):
        response_lang = requested_lang
    elif detected in ("bn", "mixed"):
        response_lang = "bn"
    else:
        response_lang = "en"

    # Classify category
    category = "general"
    for cat, pattern in _CATEGORY_PATTERNS.items():
        if pattern.search(query):
            category = cat
            break

    # Classify intent
    intent = "general"
    for intent_name, pattern in _INTENT_PATTERNS.items():
        if pattern.search(query):
            intent = intent_name
            break

    # Normalize: NFC already done in parsing; here we just strip and collapse spaces
    normalized = " ".join(query.split()).strip()

    logger.info(
        "Query analysis — lang: %s→%s, category: %s, intent: %s",
        detected, response_lang, category, intent,
    )

    return {
        "detected_language": detected,
        "response_language": response_lang,
        "normalized_query": normalized,
        "query_intent": intent,
        "query_category": category,
    }


# ---------------------------------------------------------------------------
# Node: retrieve
# ---------------------------------------------------------------------------

def retrieve(state: RAGState) -> dict[str, Any]:
    """Run BM25 + dense retrieval, apply RRF, then rerank."""
    from app.retrieval.fusion import (
        reciprocal_rank_fusion,
        build_ranked_list_from_bm25,
        build_ranked_list_from_dense,
    )
    from app.config import get_settings

    settings = get_settings()
    query = state.get("normalized_query", state.get("query", ""))
    category = state.get("query_category", None)

    # BM25
    bm25_results = []
    if _bm25_index and _bm25_index.is_ready:
        bm25_results = _bm25_index.retrieve(query, top_k=settings.bm25_top_k)
    else:
        logger.warning("BM25 index not ready.")

    # Dense
    dense_results = []
    if _dense_index and _dense_index.is_ready:
        dense_results = _dense_index.retrieve(
            query,
            top_k=settings.dense_top_k,
            category_filter=category if category != "general" else None,
        )
    else:
        logger.warning("Dense index not ready.")

    # RRF fusion
    bm25_ranked = build_ranked_list_from_bm25(bm25_results)
    dense_ranked = build_ranked_list_from_dense(dense_results)
    fused = reciprocal_rank_fusion(
        [bm25_ranked, dense_ranked],
        top_n=settings.reranker_top_k * 2,  # top 10 candidates for fast CPU reranking
    )

    # Rerank
    reranked = []
    if _reranker:
        reranked = _reranker.rerank(query, fused, top_k=settings.reranker_top_k)
    else:
        reranked = sorted(fused, key=lambda x: x[2], reverse=True)[: settings.reranker_top_k]

    logger.info(
        "Retrieval — bm25: %d, dense: %d, fused: %d, reranked: %d",
        len(bm25_results), len(dense_results), len(fused), len(reranked),
    )

    return {
        "bm25_results": bm25_results,
        "dense_results": dense_results,
        "fused_candidates": fused,
        "reranked_passages": reranked,
    }


# ---------------------------------------------------------------------------
# Node: evaluate_evidence
# ---------------------------------------------------------------------------

def evaluate_evidence(state: RAGState) -> dict[str, Any]:
    """
    Assess whether retrieved evidence is sufficient to support an answer.

    Rules:
    - If no passages: insufficient
    - If top reranker score < threshold: insufficient
    - If passages come from conflicting dates on time-sensitive info: flag it
    """
    from app.config import get_settings

    settings = get_settings()
    reranked = state.get("reranked_passages", [])
    intent = state.get("query_intent", "general")
    notes: list[str] = []

    if not reranked:
        return {
            "evidence_sufficient": False,
            "evidence_score": 0.0,
            "evidence_notes": ["No relevant passages found in the knowledge base."],
        }

    top_score = reranked[0][2] if reranked else 0.0

    # Check freshness for fee/deadline queries
    if intent == "fee":
        dates = [
            m.get("publication_date", "")
            for _, m, _ in reranked
            if m.get("publication_date")
        ]
        if not dates:
            notes.append(
                "Fee information found but source date is unknown — "
                "please verify with the official authority."
            )

    # Check for conflicting source dates
    all_dates = [m.get("publication_date", "") for _, m, _ in reranked if m.get("publication_date")]
    if len(set(all_dates)) > 1:
        notes.append(
            "Multiple source dates found; older documents may contain superseded information."
        )

    sufficient = top_score >= settings.evidence_threshold

    logger.info(
        "Evidence evaluation — top_score: %.3f, threshold: %.3f, sufficient: %s",
        top_score, settings.evidence_threshold, sufficient,
    )

    return {
        "evidence_sufficient": sufficient,
        "evidence_score": top_score,
        "evidence_notes": notes,
    }


# ---------------------------------------------------------------------------
# Node: generate_answer
# ---------------------------------------------------------------------------

def generate_answer(state: RAGState) -> dict[str, Any]:
    """Generate a grounded answer using the top retrieved passages."""
    if _generator is None:
        logger.error("Generator not initialised.")
        return {"status": "error", "error": "Generator not available.", "answer": ""}

    passages = state.get("reranked_passages", [])
    query = state.get("query", "")
    response_lang = state.get("response_language", "en")
    notes = state.get("evidence_notes", [])

    try:
        answer, citations = _generator.generate(
            query=query,
            passages=passages,
            response_language=response_lang,
        )
        limitations = list(notes)

        return {
            "answer": answer,
            "citations": citations,
            "limitations": limitations,
            "status": "answered",
        }
    except Exception as exc:
        logger.error("Generation failed: %s", exc, exc_info=True)
        return {
            "answer": "",
            "citations": [],
            "limitations": [],
            "status": "error",
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Node: fallback
# ---------------------------------------------------------------------------

def fallback(state: RAGState) -> dict[str, Any]:
    """Return a safe, honest fallback when evidence is insufficient."""
    response_lang = state.get("response_language", "en")
    notes = state.get("evidence_notes", [])

    if response_lang == "bn":
        answer = FALLBACK_BANGLA
    else:
        answer = FALLBACK_ENGLISH

    return {
        "answer": answer,
        "citations": [],
        "limitations": notes,
        "status": "insufficient_evidence",
    }

