"""
app/ingestion/parsing.py — Normalize and clean raw document text.

Responsibilities:
  - Normalize Unicode (NFC for Bangla)
  - Preserve Bangla characters, numbers, form references
  - Remove control characters while keeping meaningful whitespace
  - Detect document language
"""

from __future__ import annotations

import re
import unicodedata
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Bangla Unicode range: U+0980–U+09FF
_BANGLA_RE = re.compile(r"[\u0980-\u09FF]")
# Form/reference patterns to preserve: e.g. "Form-1", "SRO 219", "Section 4(2)(b)"
_PRESERVE_RE = re.compile(
    r"(form[-\s]?\d+[a-z]?|sro\s?\d+|section\s?\d+[\(\d\)\w\.]*|schedule\s?\w+)",
    re.IGNORECASE,
)
# Repeated whitespace collapse (but keep newlines)
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
# Repeated newlines
_MULTI_NL = re.compile(r"\n{3,}")
# Null bytes and other control chars (preserve \n, \t)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def normalize_text(text: str) -> str:
    """
    Clean and normalize document text for indexing.

    Steps:
    1. NFC Unicode normalization (essential for Bangla)
    2. Remove null bytes and control characters
    3. Collapse redundant whitespace
    4. Trim leading/trailing whitespace per line
    """
    if not text:
        return ""

    # 1. NFC normalization
    text = unicodedata.normalize("NFC", text)

    # 2. Remove control chars
    text = _CONTROL.sub("", text)

    # 3. Collapse spaces (but keep newlines)
    text = _MULTI_SPACE.sub(" ", text)

    # 4. Trim each line
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)

    # 5. Collapse 3+ blank lines to 2
    text = _MULTI_NL.sub("\n\n", text)

    return text.strip()


def detect_language(text: str) -> str:
    """
    Detect whether text is primarily Bangla or English.
    Returns 'bn' | 'en' | 'mixed' | 'unknown'.
    """
    if not text or not text.strip():
        return "unknown"

    bangla_chars = len(_BANGLA_RE.findall(text))
    ascii_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    total = bangla_chars + ascii_chars

    if total == 0:
        return "unknown"

    bangla_ratio = bangla_chars / total

    if bangla_ratio >= 0.5:
        return "bn"
    elif bangla_ratio == 0:
        return "en"
    elif bangla_ratio <= 0.2:
        return "en"
    else:
        return "mixed"


def extract_page_references(text: str) -> list[dict[str, str]]:
    """
    Extract page markers like '[Page 3]' inserted by the PDF loader.
    Returns a list of {'page': '3', 'start': char_offset} dicts.
    """
    pattern = re.compile(r"\[Page (\d+)\]")
    refs: list[dict[str, str]] = []
    for m in pattern.finditer(text):
        refs.append({"page": m.group(1), "start_char": str(m.start())})
    return refs


def extract_section_headings(text: str) -> list[str]:
    """
    Heuristically extract section headings.
    Looks for lines that are short, sentence-cased or ALL CAPS, followed by content.
    """
    headings: list[str] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # Candidate: short line (< 80 chars), followed by non-empty line
        if len(stripped) < 80 and i + 1 < len(lines) and lines[i + 1].strip():
            if stripped.isupper() or re.match(r"^[১-৯\d]+[\.\)।]", stripped):
                headings.append(stripped)
    return headings

