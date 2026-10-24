"""
app/retrieval/reranker.py — Cross-encoder reranking using BGE-reranker-v2-m3.

After RRF merging, a cross-encoder re-scores each (query, passage) pair.
This is slower but produces better relevance ordering than embedding cosine alone.

Design:
  - Lazy model loading (first call triggers download)
  - Batch scoring for efficiency
  - Returns a score in [-∞, ∞]; apply sigmoid for probability interpretation
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


class CrossEncoderReranker:
    """
    Reranks candidate chunks using a cross-encoder model.

    Supported backend: FlagEmbedding FlagReranker (BGE family).
    Falls back to passthrough (identity) if the model cannot be loaded.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3") -> None:
        self.model_name = model_name
        self._model = None
        self._available = False

    def _load(self) -> None:
        if self._model is not None:
            return

        if not self.model_name or self.model_name.lower() in ("none", "disable", "false", ""):
            logger.info("Reranker disabled by configuration (operating in RRF mode).")
            self._available = False
            return

        # Prefer sentence-transformers CrossEncoder (no pyarrow/datasets dependency)
        try:
            import torch
            from sentence_transformers import CrossEncoder  # type: ignore
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("Loading reranker via sentence-transformers: %s (device=%s)", self.model_name, device)
            self._model = CrossEncoder(self.model_name, device=device)
            self._backend = "sentence_transformers"
            self._available = True
            logger.info("Reranker loaded successfully.")
            return
        except (Exception, MemoryError) as exc:
            logger.info("sentence-transformers CrossEncoder not available/low memory (%s), trying FlagReranker…", exc)

        try:
            import torch
            has_cuda = torch.cuda.is_available()
            from FlagEmbedding import FlagReranker  # type: ignore
            logger.info("Loading reranker via FlagEmbedding: %s (fp16=%s)", self.model_name, has_cuda)
            self._model = FlagReranker(self.model_name, use_fp16=has_cuda)
            self._backend = "flagembedding"
            self._available = True
            logger.info("Reranker loaded via FlagReranker.")
        except (Exception, MemoryError) as exc:
            logger.warning(
                "Reranker not available or memory constrained (%s). Operating in RRF fusion mode.", exc
            )
            self._available = False

    def rerank(
        self,
        query: str,
        candidates: list[tuple[str, dict[str, Any], float]],
        top_k: int = 5,
    ) -> list[tuple[str, dict[str, Any], float]]:
        """
        Rerank RRF candidates and return top_k.

        Args:
            query:      User query string.
            candidates: [(chunk_id, metadata, rrf_score), ...]
            top_k:      Number of final results to keep.

        Returns:
            [(chunk_id, metadata_with_reranker_score, reranker_score), ...]
        """
        self._load()

        if not candidates:
            return []

        if not self._available or self._model is None:
            # Fallback: use RRF score as-is
            logger.warning("Reranker unavailable; using RRF scores.")
            return sorted(candidates, key=lambda x: x[2], reverse=True)[:top_k]

        pairs = [(query, meta.get("text", "")) for _, meta, _ in candidates]

        try:
            if getattr(self, "_backend", "") == "sentence_transformers":
                raw_scores = self._model.predict(pairs)
            else:
                raw_scores = self._model.compute_score(pairs, normalize=False)

            if not isinstance(raw_scores, (list, np.ndarray)):
                raw_scores = [raw_scores]

            reranked: list[tuple[str, dict, float]] = []
            for (chunk_id, meta, _), raw_score in zip(candidates, raw_scores):
                score = _sigmoid(float(raw_score))
                meta_copy = dict(meta)
                meta_copy["reranker_score"] = score
                reranked.append((chunk_id, meta_copy, score))

            reranked.sort(key=lambda x: x[2], reverse=True)
            return reranked[:top_k]

        except Exception as exc:
            logger.error("Reranker scoring failed: %s", exc)
            return sorted(candidates, key=lambda x: x[2], reverse=True)[:top_k]

    @property
    def is_available(self) -> bool:
        self._load()
        return self._available

