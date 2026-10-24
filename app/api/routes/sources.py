"""
app/api/routes/sources.py — GET /api/v1/sources/{source_id} endpoint.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.api.schemas import SourceDetailResponse, SourceRecord

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/sources/{source_id}",
    response_model=SourceDetailResponse,
    summary="Retrieve source metadata and excerpts",
)
async def get_source(source_id: str, request: Request) -> SourceDetailResponse:
    """
    Return metadata and available excerpts for a given source document.
    source_id maps to the chunk_id stored in ChromaDB / BM25.
    """
    dense_index = getattr(request.app.state, "dense_index", None)
    if dense_index is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dense index not available.",
        )

    # Look up in ChromaDB by source_id (which equals chunk_id)
    try:
        results = dense_index._collection.get(
            ids=[source_id],
            include=["documents", "metadatas"],
        )
    except Exception as exc:
        logger.error("Source lookup failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Source lookup failed.",
        )

    ids = results.get("ids", [])
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{source_id}' not found.",
        )

    meta = results["metadatas"][0]
    doc_text = results["documents"][0] if results.get("documents") else ""

    source = SourceRecord(
        source_id=source_id,
        title=meta.get("title", "Unknown"),
        authority=meta.get("authority") or None,
        url=meta.get("source_url") or None,
        category=meta.get("category", "general"),
        publication_date=meta.get("publication_date") or None,
        ingestion_date=str(meta.get("ingestion_timestamp", "")),
        chunk_count=int(meta.get("total_chunks", 0)),
        parsing_status="ok",
    )

    excerpts = [{"chunk_id": source_id, "text": doc_text, "page": meta.get("page")}]

    return SourceDetailResponse(source=source, excerpts=excerpts)

