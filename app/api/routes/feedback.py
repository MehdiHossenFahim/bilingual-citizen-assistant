"""
app/api/routes/feedback.py — POST /api/v1/feedback endpoint.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.api.schemas import FeedbackRequest, FeedbackResponse

logger = logging.getLogger(__name__)
router = APIRouter()

_FEEDBACK_FILE = Path("./data/feedback.jsonl")


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit optional response feedback",
)
async def submit_feedback(body: FeedbackRequest) -> FeedbackResponse:
    """
    Accept a helpful/not-helpful rating and optional comment.
    Stored separately from ground truth — never used to alter system behaviour.
    Sensitive: only stores query hash (not raw query) and session_id.
    """
    try:
        record = {
            "timestamp": time.time(),
            "session_id": body.session_id,
            "query_hash": body.query_hash,   # SHA-256, not raw query
            "rating": body.rating.value,
            "comment": body.comment,
        }
        _FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_FEEDBACK_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.error("Failed to write feedback: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not store feedback.",
        )

    return FeedbackResponse()

