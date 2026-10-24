"""
app/retrieval/bm25.py — Sparse BM25 retrieval using rank_bm25.

The index is serialised to disk with pickle so it survives application
restarts without requiring a full re-ingestion.

Key design decisions:
  - Tokenise for both Bangla and English using whitespace + regex
  - Store chunk IDs in parallel with BM25 corpus for traceability
  - Expose a typed retrieve() method that returns scored chunks
"""

from __future__ import annotations

import logging
import pickle
import re
from pathlib import Path
from typing import Optional

from rank_bm25 import BM25Okapi

from app.ingestion.chunking import DocumentChunk

logger = logging.getLogger(__name__)

# Bangla word boundary pattern (whitespace or punctuation)
_TOKENISE = re.compile(r"[\s\u0964\u0965,;:\.\!\?\(\)\[\]\{\}\"\']+")


def _tokenize(text: str) -> list[str]:
    """
    Whitespace-and-punctuation tokeniser that handles Bangla Unicode.
    Lowercases ASCII tokens; preserves Bangla tokens as-is.
    """
    tokens = _TOKENISE.split(text)
    result: list[str] = []
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        # Lower-case ASCII tokens; keep Bangla as-is
        if tok.isascii():
            tok = tok.lower()
        result.append(tok)
    return result


class BM25Index:
    """Manages a BM25Okapi index over DocumentChunk objects."""

    def __init__(self, index_path: str | Path) -> None:
        self.index_path = Path(index_path)
        self._bm25: Optional[BM25Okapi] = None
        self._chunk_ids: list[str] = []
        self._chunk_map: dict[str, DocumentChunk] = {}

    # ------------------------------------------------------------------
    # Building / Persisting
    # ------------------------------------------------------------------

    def build(self, chunks: list[DocumentChunk]) -> None:
        """Build the BM25 index from a list of DocumentChunk objects."""
        if not chunks:
            logger.warning("BM25: no chunks provided, index will be empty.")
            return

        corpus_tokens: list[list[str]] = []
        self._chunk_ids = []
        self._chunk_map = {}

        for chunk in chunks:
            tokens = _tokenize(chunk.text)
            corpus_tokens.append(tokens)
            self._chunk_ids.append(chunk.chunk_id)
            self._chunk_map[chunk.chunk_id] = chunk

        self._bm25 = BM25Okapi(corpus_tokens)
        logger.info("BM25: built index with %d chunks.", len(chunks))

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Incrementally add chunks and rebuild the index."""
        existing = list(self._chunk_map.values())
        self.build(existing + chunks)

    def save(self) -> None:
        """Persist the index to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "bm25": self._bm25,
            "chunk_ids": self._chunk_ids,
            "chunk_map": self._chunk_map,
        }
        with open(self.index_path, "wb") as f:
            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info("BM25: index saved to %s", self.index_path)

    def load(self) -> bool:
        """Load an existing index from disk. Returns True on success."""
        if not self.index_path.exists():
            logger.info("BM25: no existing index at %s", self.index_path)
            return False
        try:
            with open(self.index_path, "rb") as f:
                payload = pickle.load(f)
            self._bm25 = payload["bm25"]
            self._chunk_ids = payload["chunk_ids"]
            self._chunk_map = payload["chunk_map"]
            logger.info("BM25: loaded index with %d chunks.", len(self._chunk_ids))
            return True
        except Exception as exc:
            logger.error("BM25: failed to load index: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(
        self, query: str, top_k: int = 20
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Return the top-k chunks matching the query.

        Returns: list of (DocumentChunk, bm25_score) sorted descending.
        """
        if self._bm25 is None or not self._chunk_ids:
            logger.warning("BM25: index not built or loaded; returning empty results.")
            return []

        tokens = _tokenize(query)
        if not tokens:
            return []

        scores = self._bm25.get_scores(tokens)
        top_k = min(top_k, len(self._chunk_ids))

        # Get indices sorted by score descending
        ranked_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]

        results: list[tuple[DocumentChunk, float]] = []
        for idx in ranked_indices:
            if scores[idx] <= 0:
                break
            chunk_id = self._chunk_ids[idx]
            chunk = self._chunk_map.get(chunk_id)
            if chunk is not None:
                results.append((chunk, float(scores[idx])))

        return results

    @property
    def is_ready(self) -> bool:
        return self._bm25 is not None and len(self._chunk_ids) > 0

    @property
    def chunk_count(self) -> int:
        return len(self._chunk_ids)

