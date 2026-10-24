"""
app/api/routes/chat.py — POST /api/v1/chat endpoint.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    CitationModel,
    LanguageCode,
    ResponseStatus,
)
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_workflow(request: Request):
    """Dependency: retrieve the compiled RAG workflow from app state."""
    workflow = getattr(request.app.state, "workflow", None)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG workflow not initialised. Check /ready for status.",
        )
    return workflow


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Submit a bilingual citizen-services query",
    responses={
        400: {"description": "Invalid request"},
        503: {"description": "Service not ready"},
    },
)
async def chat(
    body: ChatRequest,
    request: Request,
    workflow=Depends(_get_workflow),
) -> ChatResponse:
    """
    Accept a query in Bangla or English and return a grounded answer with citations.
    """
    session_id = body.session_id or str(uuid.uuid4())

    logger.info(
        "Chat request — session: %s, language: %s, query_len: %d",
        session_id, body.language.value, len(body.query),
    )

    # Run the RAG workflow
    result = workflow.run(
        query=body.query,
        language=body.language.value,
        session_id=session_id,
    )

    # Map citations
    citations = [
        CitationModel(**c)
        for c in result.get("citations", [])
        if isinstance(c, dict)
    ]

    # Map status
    raw_status = result.get("status", "error")
    try:
        response_status = ResponseStatus(raw_status)
    except ValueError:
        response_status = ResponseStatus.ERROR

    # Map response language
    resp_lang_str = result.get("response_language", "en")
    try:
        resp_lang = LanguageCode(resp_lang_str)
    except ValueError:
        resp_lang = LanguageCode.ENGLISH

    return ChatResponse(
        answer=result.get("answer", ""),
        language=resp_lang,
        status=response_status,
        citations=citations,
        limitations=result.get("limitations", []),
        session_id=session_id,
        latency_ms=result.get("latency_ms"),
    )

