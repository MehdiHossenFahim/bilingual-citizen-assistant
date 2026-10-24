"""
tests/test_retrieval.py — Unit tests for BM25 and fusion logic.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from app.ingestion.chunking import DocumentChunk
from app.retrieval.bm25 import BM25Index, _tokenize
from app.retrieval.fusion import reciprocal_rank_fusion, build_ranked_list_from_bm25


def _make_chunk(text: str, chunk_id: str = "test-chunk-1", category: str = "passport") -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        doc_id="doc-001",
        title="Test Document",
        source_url="https://example.gov.bd/",
        authority="Test Authority",
        category=category,
        text=text,
        page=1,
    )


class TestTokenizer:
    def test_ascii_lowercased(self):
        tokens = _tokenize("Hello World")
        assert "hello" in tokens
        assert "world" in tokens

    def test_bangla_preserved(self):
        tokens = _tokenize("পাসপোর্ট আবেদন")
        assert "পাসপোর্ট" in tokens
        assert "আবেদন" in tokens

    def test_mixed_language(self):
        tokens = _tokenize("Passport করতে NID লাগে")
        assert "passport" in tokens
        assert "NID" in tokens or "nid" in tokens
        assert "করতে" in tokens

    def test_empty_string(self):
        assert _tokenize("") == []

    def test_punctuation_removed(self):
        tokens = _tokenize("Hello, World! How are you?")
        assert "hello" in tokens
        assert "world" in tokens
        assert "," not in tokens


class TestBM25Index:
    def setup_method(self, tmp_path=None):
        self.chunks = [
            _make_chunk("পাসপোর্টের জন্য NID কার্ড লাগে।", "c1"),
            _make_chunk("NID correction requires SSC certificate.", "c2", "nid"),
            _make_chunk("TIN registration is free of charge.", "c3", "tin"),
            _make_chunk("Passport renewal fee is BDT 3000.", "c4"),
        ]

    def test_build_and_retrieve(self, tmp_path):
        idx = BM25Index(tmp_path / "test.pkl")
        idx.build(self.chunks)
        assert idx.is_ready
        assert idx.chunk_count == 4

    def test_retrieve_relevant_chunk(self, tmp_path):
        idx = BM25Index(tmp_path / "test.pkl")
        idx.build(self.chunks)
        results = idx.retrieve("passport NID", top_k=4)
        assert len(results) > 0
        # Passport chunks should rank higher
        top_ids = [c.chunk_id for c, _ in results[:2]]
        assert "c1" in top_ids or "c4" in top_ids

    def test_retrieve_bangla_query(self, tmp_path):
        idx = BM25Index(tmp_path / "test.pkl")
        idx.build(self.chunks)
        results = idx.retrieve("পাসপোর্টের NID", top_k=4)
        assert len(results) > 0
        # The Bangla chunk should rank first
        assert results[0][0].chunk_id == "c1"

    def test_empty_index_returns_empty(self, tmp_path):
        idx = BM25Index(tmp_path / "test.pkl")
        results = idx.retrieve("passport", top_k=5)
        assert results == []

    def test_save_and_load(self, tmp_path):
        idx1 = BM25Index(tmp_path / "saved.pkl")
        idx1.build(self.chunks)
        idx1.save()

        idx2 = BM25Index(tmp_path / "saved.pkl")
        loaded = idx2.load()
        assert loaded is True
        assert idx2.chunk_count == 4
        results = idx2.retrieve("TIN registration free", top_k=2)
        assert results[0][0].chunk_id == "c3"


class TestRRFFusion:
    def test_basic_fusion(self):
        list_a = [("c1", {"text": "a"}), ("c2", {"text": "b"}), ("c3", {"text": "c"})]
        list_b = [("c2", {"text": "b"}), ("c1", {"text": "a"}), ("c4", {"text": "d"})]
        fused = reciprocal_rank_fusion([list_a, list_b], k=60, top_n=10)

        ids = [x[0] for x in fused]
        # c1 and c2 appear in both lists → should rank top
        assert ids[0] in ("c1", "c2")
        assert ids[1] in ("c1", "c2")

    def test_empty_lists(self):
        fused = reciprocal_rank_fusion([[], []])
        assert fused == []

    def test_single_list(self):
        list_a = [("c1", {"text": "a"}), ("c2", {"text": "b"})]
        fused = reciprocal_rank_fusion([list_a], k=60, top_n=5)
        assert fused[0][0] == "c1"

    def test_top_n_respected(self):
        list_a = [(f"c{i}", {"text": str(i)}) for i in range(20)]
        fused = reciprocal_rank_fusion([list_a], top_n=5)
        assert len(fused) == 5

    def test_scores_sum_correctly(self):
        # If item appears at rank 1 in two lists, its score should be 2*(1/(60+1))
        list_a = [("c1", {"text": "a"})]
        list_b = [("c1", {"text": "a"})]
        fused = reciprocal_rank_fusion([list_a, list_b], k=60)
        expected = 2.0 / (60 + 1)
        assert abs(fused[0][2] - expected) < 1e-9

    def test_bm25_ranked_list_conversion(self):
        chunk = _make_chunk("some text", "c1")
        bm25_results = [(chunk, 0.8)]
        ranked = build_ranked_list_from_bm25(bm25_results)
        assert ranked[0][0] == "c1"
        assert "text" in ranked[0][1]
        assert ranked[0][1]["bm25_score"] == 0.8

