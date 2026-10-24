"""
tests/test_citations.py — Tests for citation extraction and validation.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


class TestCitationExtraction:
    """Test that citations are correctly extracted from generated answers."""

    def _make_passages(self):
        return [
            (
                "chunk-001",
                {
                    "chunk_id": "chunk-001",
                    "title": "Passport Application Guide",
                    "authority": "DIP",
                    "source_url": "https://www.dip.gov.bd/",
                    "page": 3,
                    "section": None,
                    "publication_date": "2024-01-01",
                    "text": "NID is required for new passport applications.",
                },
                0.85,
            ),
            (
                "chunk-002",
                {
                    "chunk_id": "chunk-002",
                    "title": "Passport Fees Schedule",
                    "authority": "DIP",
                    "source_url": "https://www.dip.gov.bd/fees/",
                    "page": 1,
                    "section": "Fee Table",
                    "publication_date": "2024-01-01",
                    "text": "Regular passport fee is BDT 3,000 for 48-page.",
                },
                0.78,
            ),
        ]

    def test_citation_contains_required_fields(self):
        from app.generation.generator import AnswerGenerator
        gen = AnswerGenerator(api_key="fake", model="gemini-3.8-flash")

        answer = "You need an NID [src-1]. The fee is BDT 3,000 [src-2]."
        passages = self._make_passages()
        citations = gen._extract_citations(answer, passages)

        assert len(citations) >= 1
        for cit in citations:
            assert "source_id" in cit
            assert "title" in cit
            assert "url" in cit

    def test_valid_url_passes(self):
        from app.generation.generator import _is_valid_url
        assert _is_valid_url("https://www.dip.gov.bd/") is True
        assert _is_valid_url("http://services.nidw.gov.bd/") is True

    def test_invalid_url_rejected(self):
        from app.generation.generator import _is_valid_url
        assert _is_valid_url("") is False
        assert _is_valid_url("ftp://files.example.com") is False
        assert _is_valid_url("not-a-url") is False
        assert _is_valid_url(None) is False

    def test_truncate_long_excerpt(self):
        from app.generation.generator import _truncate
        long_text = "word " * 200
        result = _truncate(long_text, 100)
        assert len(result) <= 104  # slight tolerance for word boundary
        assert result.endswith("…")

    def test_short_excerpt_unchanged(self):
        from app.generation.generator import _truncate
        short = "This is a short text."
        assert _truncate(short, 100) == short

    def test_top3_passages_always_included(self):
        """Even if not cited in text, top 3 passages should appear in citations."""
        from app.generation.generator import AnswerGenerator
        gen = AnswerGenerator(api_key="fake", model="gemini-3.8-flash")
        # Answer with no explicit citation markers
        answer = "You should contact the passport office for more information."
        passages = self._make_passages()
        citations = gen._extract_citations(answer, passages)
        # Both passages are in top 3 → both should be included
        assert len(citations) == 2

    def test_citation_source_id_matches_chunk_id(self):
        from app.generation.generator import AnswerGenerator
        gen = AnswerGenerator(api_key="fake", model="gemini-3.8-flash")
        answer = "NID is required [src-1]."
        passages = self._make_passages()
        citations = gen._extract_citations(answer, passages)
        cited_ids = {c["source_id"] for c in citations}
        assert "chunk-001" in cited_ids


class TestCitationAPISchema:
    """Test that CitationModel validates correctly."""

    def test_citation_model_valid(self):
        from app.api.schemas import CitationModel
        cit = CitationModel(
            source_id="chunk-001",
            title="Passport Guide",
            authority="DIP",
            url="https://www.dip.gov.bd/",
            page=3,
            excerpt="NID is required.",
            publication_date="2024-01-01",
        )
        assert cit.source_id == "chunk-001"
        assert cit.page == 3

    def test_citation_model_optional_fields(self):
        from app.api.schemas import CitationModel
        cit = CitationModel(source_id="c1", title="Doc")
        assert cit.url is None
        assert cit.page is None

