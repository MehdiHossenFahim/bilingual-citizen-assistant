"""
tests/test_fallback.py — Tests for fallback behaviour on insufficient evidence.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


class TestFallbackNode:
    """Test the fallback LangGraph node directly."""

    def test_fallback_english_response(self):
        from app.graph.nodes import fallback
        from app.generation.prompts import FALLBACK_ENGLISH

        state = {
            "response_language": "en",
            "evidence_notes": ["No relevant passages found."],
        }
        result = fallback(state)
        assert result["status"] == "insufficient_evidence"
        assert FALLBACK_ENGLISH in result["answer"]
        assert result["citations"] == []

    def test_fallback_bangla_response(self):
        from app.graph.nodes import fallback
        from app.generation.prompts import FALLBACK_BANGLA

        state = {
            "response_language": "bn",
            "evidence_notes": [],
        }
        result = fallback(state)
        assert result["status"] == "insufficient_evidence"
        assert FALLBACK_BANGLA in result["answer"]

    def test_fallback_includes_evidence_notes(self):
        from app.graph.nodes import fallback

        notes = ["Source date unknown.", "Conflicting documents found."]
        state = {
            "response_language": "en",
            "evidence_notes": notes,
        }
        result = fallback(state)
        assert result["limitations"] == notes


class TestEvidenceEvaluationNode:
    """Test the evaluate_evidence node routing logic."""

    def _run_eval(self, passages, intent="general"):
        from app.graph.nodes import evaluate_evidence
        return evaluate_evidence(
            {
                "reranked_passages": passages,
                "query_intent": intent,
            }
        )

    def test_no_passages_triggers_fallback(self):
        result = self._run_eval([])
        assert result["evidence_sufficient"] is False
        assert result["evidence_score"] == 0.0
        assert len(result["evidence_notes"]) > 0

    def test_high_score_passage_is_sufficient(self):
        passages = [
            ("c1", {"title": "Doc", "text": "NID required.", "publication_date": "2024-01-01"}, 0.85)
        ]
        result = self._run_eval(passages)
        # With default threshold of 0.40, score 0.85 should be sufficient
        assert result["evidence_sufficient"] is True
        assert result["evidence_score"] == 0.85

    def test_low_score_triggers_fallback(self):
        passages = [
            ("c1", {"title": "Doc", "text": "Maybe relevant.", "publication_date": ""}, 0.10)
        ]
        result = self._run_eval(passages)
        assert result["evidence_sufficient"] is False

    def test_fee_intent_without_date_adds_warning(self):
        passages = [
            ("c1", {"title": "Fee Schedule", "text": "Fee is 3000.", "publication_date": ""}, 0.90)
        ]
        result = self._run_eval(passages, intent="fee")
        notes = result["evidence_notes"]
        assert any("fee" in n.lower() or "date" in n.lower() for n in notes)

    def test_conflicting_dates_flagged(self):
        passages = [
            ("c1", {"title": "Doc A", "text": "a", "publication_date": "2022-01-01"}, 0.80),
            ("c2", {"title": "Doc B", "text": "b", "publication_date": "2024-06-01"}, 0.75),
        ]
        result = self._run_eval(passages)
        notes = result["evidence_notes"]
        assert any("date" in n.lower() or "superseded" in n.lower() for n in notes)


class TestQueryAnalysisNode:
    """Test query language detection and category classification."""

    def _run_analysis(self, query, language="auto"):
        from app.graph.nodes import analyze_query
        return analyze_query({"query": query, "language": language})

    def test_english_query_detected(self):
        result = self._run_analysis("How do I apply for a passport?")
        assert result["detected_language"] == "en"
        assert result["query_category"] == "passport"

    def test_bangla_query_detected(self):
        result = self._run_analysis("পাসপোর্টের জন্য কী কী লাগে?")
        assert result["detected_language"] == "bn"
        assert result["query_category"] == "passport"

    def test_nid_category_detected(self):
        result = self._run_analysis("NID correction process in Bangladesh")
        assert result["query_category"] == "nid"

    def test_tin_category_detected(self):
        result = self._run_analysis("TIN registration is free")
        assert result["query_category"] == "tin"

    def test_explicit_language_overrides_detection(self):
        result = self._run_analysis("passport documents", language="bn")
        assert result["response_language"] == "bn"

    def test_query_normalized(self):
        result = self._run_analysis("  passport   documents  ")
        assert result["normalized_query"] == "passport documents"

    def test_out_of_domain_classified_general(self):
        result = self._run_analysis("What is the weather in Dhaka?")
        assert result["query_category"] == "general"


class TestFallbackMessages:
    """Test that fallback messages are non-empty, honest, and language-appropriate."""

    def test_bangla_fallback_not_empty(self):
        from app.generation.prompts import FALLBACK_BANGLA
        assert len(FALLBACK_BANGLA) > 50
        # Should contain Bangla characters
        assert any("\u0980" <= c <= "\u09FF" for c in FALLBACK_BANGLA)

    def test_english_fallback_not_empty(self):
        from app.generation.prompts import FALLBACK_ENGLISH
        assert len(FALLBACK_ENGLISH) > 50
        # Should not fabricate a specific answer
        assert "verify" in FALLBACK_ENGLISH.lower() or "cannot" in FALLBACK_ENGLISH.lower()

    def test_fallback_does_not_contain_fake_url(self):
        from app.generation.prompts import FALLBACK_BANGLA, FALLBACK_ENGLISH
        for msg in [FALLBACK_BANGLA, FALLBACK_ENGLISH]:
            assert "http://fake" not in msg
            assert "www.example" not in msg

