"""
app/ingestion/chunking.py — Split normalized documents into indexable chunks.

Strategy:
  - Recursive character splitting with Bangla-aware sentence boundaries
  - Preserve page references and section headings in chunk metadata
  - Guarantee every chunk is traceable to its source document
"""

from __future__ import annotations

import hashlib
import re
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

from app.ingestion.loaders import RawDocument
from app.ingestion.parsing import normalize_text, detect_language, extract_page_references

logger = logging.getLogger(__name__)

# Sentence-boundary patterns covering:
#   - English: . ! ?
#   - Bangla danda: ।  double danda: ॥
_SENT_BOUNDARY = re.compile(r"(?<=[।॥\.\!\?])\s+")

DEFAULT_CHUNK_SIZE = 512     # characters (not tokens)
DEFAULT_CHUNK_OVERLAP = 80   # characters


@dataclass
class DocumentChunk:
    """A single indexable unit derived from a RawDocument."""

    chunk_id: str
    doc_id: str
    title: str
    source_url: Optional[str]
    authority: Optional[str]
    category: str
    text: str
    page: Optional[int] = None
    section: Optional[str] = None
    publication_date: Optional[str] = None
    ingestion_timestamp: float = field(default_factory=time.time)
    language: str = "unknown"
    chunk_index: int = 0
    total_chunks: int = 0

    def to_metadata_dict(self) -> dict:
        """Serialise metadata for ChromaDB / BM25 storage."""
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "title": self.title,
            "source_url": self.source_url or "",
            "authority": self.authority or "",
            "category": self.category,
            "page": self.page or 0,
            "section": self.section or "",
            "publication_date": self.publication_date or "",
            "ingestion_timestamp": self.ingestion_timestamp,
            "language": self.language,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
        }


class DocumentChunker:
    """
    Split a RawDocument into overlapping text chunks.

    Overlap ensures that sentences split across chunk boundaries still
    appear in at least one chunk's context window.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc: RawDocument) -> list[DocumentChunk]:
        """Return a list of DocumentChunk objects for the given RawDocument."""
        if not doc.raw_text:
            logger.warning("Document %s has empty text, skipping chunking.", doc.doc_id)
            return []

        normalized = normalize_text(doc.raw_text)
        page_refs = extract_page_references(normalized)

        # Split into raw chunks
        raw_chunks = self._split(normalized)

        chunks: list[DocumentChunk] = []
        for i, text in enumerate(raw_chunks):
            chunk_id = self._make_chunk_id(doc.doc_id, i)

            # Determine page number from page refs
            page = self._find_page(text, page_refs)

            # Detect language per chunk
            lang = detect_language(text)

            chunk = DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc.doc_id,
                title=doc.title,
                source_url=doc.source_url,
                authority=doc.authority,
                category=doc.category,
                text=text,
                page=page,
                publication_date=doc.publication_date,
                ingestion_timestamp=doc.ingestion_timestamp,
                language=lang,
                chunk_index=i,
                total_chunks=len(raw_chunks),
            )
            chunks.append(chunk)

        # Back-fill total_chunks
        for c in chunks:
            c.total_chunks = len(chunks)

        logger.info(
            "Chunked doc %s (%s) → %d chunks",
            doc.doc_id, doc.title[:40], len(chunks)
        )
        return chunks

    def _split(self, text: str) -> list[str]:
        """Recursively split text into chunks with overlap."""
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            if end >= len(text):
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # Try to split at sentence boundary within the window
            window = text[start:end]
            split_pos = self._find_split_pos(window)

            chunk = text[start : start + split_pos].strip()
            if chunk:
                chunks.append(chunk)

            # Move forward (minus overlap)
            start = start + split_pos - self.chunk_overlap
            if start < 0:
                start = 0

        return chunks

    def _find_split_pos(self, window: str) -> int:
        """Find the best position to split within a window."""
        # Prefer sentence boundary in the last 30% of the window
        threshold = int(len(window) * 0.7)
        boundaries = list(_SENT_BOUNDARY.finditer(window))

        for m in reversed(boundaries):
            if m.start() >= threshold:
                return m.start()

        # Fall back to newline
        nl_pos = window.rfind("\n", threshold)
        if nl_pos != -1:
            return nl_pos

        # Fall back to space
        sp_pos = window.rfind(" ", threshold)
        if sp_pos != -1:
            return sp_pos

        return len(window)

    @staticmethod
    def _make_chunk_id(doc_id: str, index: int) -> str:
        raw = f"{doc_id}::{index}"
        return hashlib.sha256(raw.encode()).hexdigest()[:20]

    @staticmethod
    def _find_page(text: str, page_refs: list[dict]) -> Optional[int]:
        """Return the page number most relevant to this chunk's text."""
        page_pattern = re.compile(r"\[Page (\d+)\]")
        m = page_pattern.search(text)
        if m:
            return int(m.group(1))
        return None

