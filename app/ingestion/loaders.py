"""
app/ingestion/loaders.py — Load raw documents from URLs or local files.

Supports:
  - PDF files (pypdf)
  - HTML pages (requests + BeautifulSoup)
  - JSON/JSONL structured FAQ datasets
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class RawDocument:
    """Represents a loaded-but-not-yet-chunked document."""

    doc_id: str
    title: str
    source_url: Optional[str]
    authority: Optional[str]
    category: str                    # passport | nid | tin | general
    raw_text: str
    publication_date: Optional[str]
    ingestion_timestamp: float = field(default_factory=time.time)
    file_type: str = "unknown"
    parsing_status: str = "ok"
    parsing_notes: str = ""

    def __post_init__(self) -> None:
        if not self.doc_id:
            # Auto-generate deterministic ID from URL or title
            seed = self.source_url or self.title
            self.doc_id = hashlib.sha256(seed.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# HTML Loader
# ---------------------------------------------------------------------------

class HTMLLoader:
    """Load text from a public URL via requests + BeautifulSoup."""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; CitizenAssistantBot/1.0; "
            "+https://github.com/your-org/bilingual-citizen-assistant)"
        )
    }
    TIMEOUT = 30

    def load(
        self,
        url: str,
        title: str,
        authority: Optional[str] = None,
        category: str = "general",
        publication_date: Optional[str] = None,
    ) -> RawDocument:
        doc_id = hashlib.sha256(url.encode()).hexdigest()[:16]
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # Remove scripts, styles, nav
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            text = self._clean_text(text)

            return RawDocument(
                doc_id=doc_id,
                title=title,
                source_url=url,
                authority=authority,
                category=category,
                raw_text=text,
                publication_date=publication_date,
                file_type="html",
                parsing_status="ok",
            )
        except requests.RequestException as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
            return RawDocument(
                doc_id=doc_id,
                title=title,
                source_url=url,
                authority=authority,
                category=category,
                raw_text="",
                publication_date=publication_date,
                file_type="html",
                parsing_status="failed",
                parsing_notes=str(exc),
            )

    @staticmethod
    def _clean_text(text: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        # Remove blank runs > 2
        result, blank_run = [], 0
        for line in lines:
            if not line:
                blank_run += 1
                if blank_run <= 2:
                    result.append(line)
            else:
                blank_run = 0
                result.append(line)
        return "\n".join(result)


# ---------------------------------------------------------------------------
# PDF Loader
# ---------------------------------------------------------------------------

class PDFLoader:
    """Extract text from local PDF files using pypdf."""

    def load(
        self,
        file_path: str | Path,
        title: str,
        source_url: Optional[str] = None,
        authority: Optional[str] = None,
        category: str = "general",
        publication_date: Optional[str] = None,
    ) -> RawDocument:
        from pypdf import PdfReader  # lazy import

        path = Path(file_path)
        doc_id = hashlib.sha256(str(path).encode()).hexdigest()[:16]

        if not path.exists():
            return RawDocument(
                doc_id=doc_id,
                title=title,
                source_url=source_url,
                authority=authority,
                category=category,
                raw_text="",
                publication_date=publication_date,
                file_type="pdf",
                parsing_status="failed",
                parsing_notes=f"File not found: {path}",
            )

        try:
            reader = PdfReader(str(path))
            pages_text: list[str] = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages_text.append(f"[Page {i + 1}]\n{page_text}")
            full_text = "\n\n".join(pages_text)

            return RawDocument(
                doc_id=doc_id,
                title=title,
                source_url=source_url,
                authority=authority,
                category=category,
                raw_text=full_text,
                publication_date=publication_date,
                file_type="pdf",
                parsing_status="ok",
            )
        except Exception as exc:
            logger.error("PDF parsing failed for %s: %s", path, exc)
            return RawDocument(
                doc_id=doc_id,
                title=title,
                source_url=source_url,
                authority=authority,
                category=category,
                raw_text="",
                publication_date=publication_date,
                file_type="pdf",
                parsing_status="failed",
                parsing_notes=str(exc),
            )


# ---------------------------------------------------------------------------
# JSON FAQ Loader
# ---------------------------------------------------------------------------

class JSONFAQLoader:
    """
    Load structured FAQ/knowledge documents from JSON files.

    Expected schema per record:
    {
        "id": "optional-unique-id",
        "title": "Document or question title",
        "content": "Body text",
        "source_url": "https://...",
        "authority": "Department of Immigration & Passports",
        "category": "passport",
        "publication_date": "2024-01-15"
    }
    """

    def load_file(self, file_path: str | Path) -> list[RawDocument]:
        path = Path(file_path)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                data = [data]

            docs: list[RawDocument] = []
            seen_ids: set[str] = set()

            for i, record in enumerate(data):
                if not isinstance(record, dict):
                    continue

                content = record.get("content", "") or record.get("text", "")
                if not content:
                    logger.warning("Record %d in %s has no content, skipping.", i, path)
                    continue

                raw_id = record.get("id") or f"{path.stem}_{i}"
                doc_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]

                if doc_id in seen_ids:
                    logger.warning("Duplicate doc_id %s, skipping.", doc_id)
                    continue
                seen_ids.add(doc_id)

                docs.append(
                    RawDocument(
                        doc_id=doc_id,
                        title=record.get("title", f"Record {i + 1}"),
                        source_url=record.get("source_url"),
                        authority=record.get("authority"),
                        category=record.get("category", "general"),
                        raw_text=content,
                        publication_date=record.get("publication_date"),
                        file_type="json",
                    )
                )
            return docs
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load JSON file %s: %s", path, exc)
            return []

