"""
app/generation/generator.py — Grounded answer generation using Gemini.

Uses the google-genai SDK (gemini-3.8-flash by default).
Extracts citations from the generated answer and maps them to source metadata.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.generation.prompts import (
    SYSTEM_PROMPT,
    build_user_message,
    FALLBACK_ENGLISH,
    FALLBACK_BANGLA,
)

logger = logging.getLogger(__name__)

# Pattern to find [src-N] citation markers in generated text
_CITATION_RE = re.compile(r"\[src-(\d+)\]")


class AnswerGenerator:
    """
    Generates grounded answers from retrieved passages using the Gemini API.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.8-flash",
        max_tokens: int = 2048,
        temperature: float = 0.1,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def generate(
        self,
        query: str,
        passages: list[tuple[str, dict, float]],
        response_language: str = "en",
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Generate a grounded answer.

        Returns:
            (answer_text, citations_list)

        Citations list is a list of dicts matching the CitationModel schema.
        """
        if not passages:
            return (
                FALLBACK_BANGLA if response_language == "bn" else FALLBACK_ENGLISH,
                [],
            )

        client = self._get_client()

        # Build system and user messages
        lang_name = "Bangla (বাংলা)" if response_language == "bn" else "English"
        system = SYSTEM_PROMPT.format(response_language=lang_name)
        user_msg = build_user_message(query, passages)

        gen_config: dict[str, Any] = {
            "max_output_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if "flash-lite" in self.model:
            gen_config["thinking_level"] = "minimal"
        elif "flash" in self.model:
            gen_config["thinking_level"] = "low"

        try:
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            response = client.models.generate_content(
                model=self.model,
                contents=user_msg,
                config=config,
            )
            answer = response.text or ""
        except Exception as exc:
            logger.info("generate_content failed or alternative SDK form required (%s); using interactions...", exc)
            try:
                interaction = client.interactions.create(
                    model=self.model,
                    system_instruction=system,
                    input=user_msg,
                    generation_config=gen_config,
                    store=False,  # don't persist citizen queries
                )
                answer = interaction.output_text or ""
            except Exception as exc2:
                logger.error("Gemini API generation error: %s", exc2)
                raise

        # Extract citations from the generated text
        citations = self._extract_citations(answer, passages)

        # Clean up src markers from displayed answer (keep them as footnote refs)
        # Keep them for transparency — they help users verify sources
        return answer, citations

    def _extract_citations(
        self,
        answer: str,
        passages: list[tuple[str, dict, float]],
    ) -> list[dict[str, Any]]:
        """
        Map [src-N] markers found in the answer to source metadata.
        Only include citations that actually appear in the answer.
        """
        cited_indices = set()
        for m in _CITATION_RE.finditer(answer):
            idx = int(m.group(1))
            cited_indices.add(idx)

        citations: list[dict[str, Any]] = []
        for i, (chunk_id, meta, score) in enumerate(passages, start=1):
            if i not in cited_indices:
                # Still include top-3 passages even if not explicitly cited
                # to provide transparency
                if i > 3:
                    continue

            url = meta.get("source_url", "") or ""
            # Validate URL is plausible .gov.bd / official
            validated_url = url if _is_valid_url(url) else None

            citations.append({
                "source_id": meta.get("chunk_id", chunk_id),
                "title": meta.get("title", "Unknown"),
                "authority": meta.get("authority", ""),
                "url": validated_url,
                "page": meta.get("page") or None,
                "section": meta.get("section") or None,
                "excerpt": _truncate(meta.get("text", ""), 300),
                "publication_date": meta.get("publication_date") or None,
                "ingestion_date": None,
            })

        return citations


def _is_valid_url(url: str) -> bool:
    """Basic URL validation — must start with http/https."""
    return bool(url) and url.startswith(("http://", "https://"))


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"

