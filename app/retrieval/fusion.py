"""
app/retrieval/fusion.py — Reciprocal Rank Fusion (RRF) to merge BM25 and dense results.

RRF formula: RRF(d, k=60) = Σ 1 / (k + rank_i)

Design decisions:
  - k=60 is the standard default, but is configurable
  - Chunk IDs are used as the canonical join key
  - Metadata is carried forward from whichever list saw the chunk
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    ranked_lists: list[list[tuple[str, dict[str, Any]]]],
    k: int = 60,
    top_n: int = 30,
) -> list[tuple[str, dict[str, Any], float]]:
    """
    Merge multiple ranked lists using Reciprocal Rank Fusion.

    Args:
        ranked_lists: Each list is [(chunk_id, metadata_dict), ...] sorted best-first.
        k:            RRF constant (default 60).
        top_n:        Number of results to return.

    Returns:
        [(chunk_id, metadata_dict, rrf_score), ...] sorted descending.
    """
    scores: dict[str, float] = {}
    metadata_store: dict[str, dict[str, Any]] = {}

    for ranked in ranked_lists:
        for rank, (chunk_id, meta) in enumerate(ranked, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
            # Prefer metadata that includes actual text
            if chunk_id not in metadata_store or "text" in meta:
                metadata_store[chunk_id] = meta

    sorted_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)

    result: list[tuple[str, dict[str, Any], float]] = []
    for cid in sorted_ids[:top_n]:
        result.append((cid, metadata_store[cid], scores[cid]))

    logger.debug("RRF: merged %d candidates → top %d", len(scores), len(result))
    return result


def build_ranked_list_from_bm25(
    bm25_results: list[tuple[Any, float]],
) -> list[tuple[str, dict]]:
    """Convert BM25 (DocumentChunk, score) tuples to (chunk_id, metadata) pairs."""
    ranked: list[tuple[str, dict]] = []
    for chunk, score in bm25_results:
        meta = chunk.to_metadata_dict()
        meta["text"] = chunk.text
        meta["bm25_score"] = score
        ranked.append((chunk.chunk_id, meta))
    return ranked


def build_ranked_list_from_dense(
    dense_results: list[tuple[dict, float]],
) -> list[tuple[str, dict]]:
    """Convert dense (metadata_dict, similarity) tuples to (chunk_id, metadata) pairs."""
    ranked: list[tuple[str, dict]] = []
    for meta, sim in dense_results:
        meta_copy = dict(meta)
        meta_copy["dense_score"] = sim
        chunk_id = meta_copy.get("chunk_id", "")
        if chunk_id:
            ranked.append((chunk_id, meta_copy))
    return ranked

