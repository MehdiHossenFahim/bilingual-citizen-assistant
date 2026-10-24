"""
app/api/schemas.py — Pydantic request/response models for the API.

All public models are validated strictly. Internal fields use Optional with
safe defaults to avoid leaking server internals in error payloads.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class LanguageCode(str, Enum):
    BANGLA = "bn"
    ENGLISH = "en"
    AUTO = "auto"      # detect automatically


class ResponseStatus(str, Enum):
    ANSWERED = "answered"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CLARIFICATION_NEEDED = "clarification_needed"
    ERROR = "error"


class FeedbackRating(str, Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="User question in Bangla, English, or Banglish",
    )
    language: LanguageCode = Field(
        LanguageCode.AUTO,
        description="Preferred response language; 'auto' detects from query",
    )
    session_id: Optional[str] = Field(
        None,
        max_length=128,
        description="Optional session identifier for conversation context",
    )

    @field_validator("query")
    @classmethod
    def _strip_query(cls, v: str) -> str:
        return v.strip()


class CitationModel(BaseModel):
    source_id: str = Field(..., description="Internal unique source record ID")
    title: str = Field(..., description="Document title")
    authority: Optional[str] = Field(None, description="Issuing government authority")
    url: Optional[str] = Field(None, description="Official source URL")
    page: Optional[int] = Field(None, description="Page number in source document")
    section: Optional[str] = Field(None, description="Section or heading reference")
    excerpt: Optional[str] = Field(None, max_length=500, description="Supporting passage snippet")
    publication_date: Optional[str] = Field(None, description="Document publication/effective date")
    ingestion_date: Optional[str] = Field(None, description="Date source was indexed")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generated answer text")
    language: LanguageCode = Field(..., description="Language of the response")
    status: ResponseStatus = Field(..., description="Outcome status")
    citations: list[CitationModel] = Field(default_factory=list)
    limitations: list[str] = Field(
        default_factory=list,
        description="Caveats, freshness warnings, or unresolved conflicts",
    )
    session_id: Optional[str] = None
    latency_ms: Optional[float] = Field(None, description="Server-side processing time in ms")


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

class SourceRecord(BaseModel):
    source_id: str
    title: str
    authority: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    publication_date: Optional[str] = None
    ingestion_date: Optional[str] = None
    chunk_count: int = 0
    parsing_status: str = "ok"


class SourceDetailResponse(BaseModel):
    source: SourceRecord
    excerpts: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    session_id: str = Field(..., max_length=128)
    query_hash: str = Field(..., description="SHA-256 of the submitted query")
    rating: FeedbackRating
    comment: Optional[str] = Field(None, max_length=500)


class FeedbackResponse(BaseModel):
    acknowledged: bool = True
    message: str = "Thank you for your feedback."


# ---------------------------------------------------------------------------
# Health / Readiness
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ReadinessResponse(BaseModel):
    ready: bool
    checks: dict[str, str] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Error
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    details: list[ErrorDetail] = Field(default_factory=list)
    request_id: Optional[str] = None

