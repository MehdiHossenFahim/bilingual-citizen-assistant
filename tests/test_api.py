"""
tests/test_api.py — FastAPI endpoint integration tests.
Uses TestClient (httpx) without starting a real server.
"""

from __future__ import annotations

import json
import os
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("GEMINI_API_KEY", "test-api-key-not-real")

from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def mock_workflow():
    """Provide a mock RAGWorkflow that returns predictable responses."""
    workflow = MagicMock()
    workflow.run.return_value = {
        "answer": "You need an NID and application form.",
        "response_language": "en",
        "status": "answered",
        "citations": [
            {
                "source_id": "chunk-001",
                "title": "Passport Application Guide",
                "authority": "DIP",
                "url": "https://www.dip.gov.bd/",
                "page": 1,
                "section": None,
                "excerpt": "NID is required for passport application.",
                "publication_date": "2024-01-01",
                "ingestion_date": None,
            }
        ],
        "limitations": [],
        "latency_ms": 1234.5,
    }
    return workflow


@pytest.fixture(scope="module")
def client(mock_workflow):
    from app.main import app
    app.state.workflow = mock_workflow
    app.state.bm25_index = MagicMock(is_ready=True, chunk_count=50)
    app.state.dense_index = MagicMock(is_ready=True, vector_count=50)
    app.state.reranker = MagicMock()
    app.state.generator = MagicMock()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestHealthEndpoints:
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_ready_returns_structure(self, client):
        r = client.get("/ready")
        assert r.status_code == 200
        data = r.json()
        assert "ready" in data
        assert "checks" in data


class TestChatEndpoint:
    def test_valid_english_query(self, client):
        r = client.post(
            "/api/v1/chat",
            json={"query": "How do I apply for a passport?", "language": "en"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert "status" in data
        assert "citations" in data
        assert data["status"] in ["answered", "insufficient_evidence", "error"]

    def test_valid_bangla_query(self, client):
        r = client.post(
            "/api/v1/chat",
            json={"query": "পাসপোর্ট করতে কী লাগে?", "language": "bn"},
        )
        assert r.status_code == 200

    def test_short_query_rejected(self, client):
        r = client.post("/api/v1/chat", json={"query": "a", "language": "en"})
        assert r.status_code == 422

    def test_empty_query_rejected(self, client):
        r = client.post("/api/v1/chat", json={"query": "", "language": "en"})
        assert r.status_code == 422

    def test_too_long_query_rejected(self, client):
        r = client.post("/api/v1/chat", json={"query": "x" * 1001, "language": "en"})
        assert r.status_code == 422

    def test_invalid_language_rejected(self, client):
        r = client.post(
            "/api/v1/chat", json={"query": "valid query text", "language": "de"}
        )
        assert r.status_code == 422

    def test_auto_language_accepted(self, client):
        r = client.post(
            "/api/v1/chat", json={"query": "How do I get a TIN?", "language": "auto"}
        )
        assert r.status_code == 200

    def test_session_id_returned(self, client):
        r = client.post(
            "/api/v1/chat",
            json={
                "query": "How do I apply for NID correction?",
                "language": "en",
                "session_id": "test-session-123",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["session_id"] == "test-session-123"

    def test_response_has_required_fields(self, client):
        r = client.post(
            "/api/v1/chat",
            json={"query": "What documents do I need for a passport?", "language": "en"},
        )
        data = r.json()
        assert "answer" in data
        assert "language" in data
        assert "status" in data
        assert "citations" in data
        assert "limitations" in data

    def test_missing_query_field_rejected(self, client):
        r = client.post("/api/v1/chat", json={"language": "en"})
        assert r.status_code == 422


class TestFeedbackEndpoint:
    def test_valid_feedback_accepted(self, client, tmp_path, monkeypatch):
        import app.api.routes.feedback as fb_module
        monkeypatch.setattr(fb_module, "_FEEDBACK_FILE", tmp_path / "feedback.jsonl")
        r = client.post(
            "/api/v1/feedback",
            json={
                "session_id": "sess-abc",
                "query_hash": "abc123def456",
                "rating": "helpful",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["acknowledged"] is True

    def test_feedback_invalid_rating(self, client):
        r = client.post(
            "/api/v1/feedback",
            json={
                "session_id": "sess-abc",
                "query_hash": "abc123",
                "rating": "super_helpful",
            },
        )
        assert r.status_code == 422

