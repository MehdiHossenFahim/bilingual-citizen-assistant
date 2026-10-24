"""
app/retrieval/dense_search.py — Multilingual dense retrieval with BGE-M3.

Uses BAAI/bge-m3 via FlagEmbedding for generating embeddings, and
ChromaDB as the vector store.

Design decisions:
  - Model is loaded once (singleton) for efficiency
  - Embeddings are normalised (L2) before storage for cosine similarity
  - Metadata is stored alongside vectors for traceability
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np

from app.ingestion.chunking import DocumentChunk

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Singleton wrapper for BAAI/bge-m3 via FlagEmbedding."""

    _instance: Optional["EmbeddingModel"] = None

    def __new__(cls, model_name: str = "BAAI/bge-m3") -> "EmbeddingModel":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model_name = model_name
            cls._instance._model = None
        return cls._instance

    def _load(self) -> None:
        if self._model is not None:
            return

        # 1. Cloud-hosted Gemini Embeddings (Zero RAM footprint — ideal for 512MB cloud free tiers)
        if "gemini" in self._model_name.lower() or "text-embedding" in self._model_name.lower():
            try:
                from google import genai
                from app.config import get_settings
                settings = get_settings()
                self._model = genai.Client(api_key=settings.gemini_api_key)
                self._backend = "gemini"
                logger.info("Using zero-RAM cloud embeddings via Gemini API: %s", self._model_name)
                return
            except Exception as exc:
                logger.error("Failed to initialize Gemini cloud embeddings: %s", exc)
                raise

        # 2. Local SentenceTransformer with automatic low-RAM fallback
        try:
            import torch
            from sentence_transformers import SentenceTransformer  # type: ignore
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("Loading embedding model via sentence-transformers: %s (device=%s)", self._model_name, device)
            self._model = SentenceTransformer(self._model_name, device=device)
            self._backend = "sentence_transformers"
            logger.info("Embedding model loaded successfully.")
            return
        except (Exception, MemoryError) as exc:
            logger.warning(
                "Local model '%s' failed or memory constrained (%s). Auto-fallback to zero-RAM 'gemini-embedding-001' to prevent server OOM.",
                self._model_name, exc,
            )
            try:
                from google import genai
                from app.config import get_settings
                settings = get_settings()
                self._model = genai.Client(api_key=settings.gemini_api_key)
                self._model_name = "gemini-embedding-001"
                self._backend = "gemini"
                logger.info("Auto-fallback to zero-RAM gemini-embedding-001 active.")
                return
            except Exception as e2:
                logger.error("Fallback to Gemini embeddings failed: %s", e2)
                raise exc

    def encode(self, texts: list[str], batch_size: int = 12) -> np.ndarray:
        """
        Encode a list of texts.
        Returns float32 array of shape (N, dim), L2-normalised.
        """
        self._load()

        # Gemini Cloud API backend (Zero RAM)
        if getattr(self, "_backend", "") == "gemini":
            embeddings_list: list[list[float]] = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                res = self._model.models.embed_content(
                    model=self._model_name,
                    contents=batch,
                )
                if hasattr(res, "embeddings") and res.embeddings:
                    for emb in res.embeddings:
                        embeddings_list.append(emb.values)
                elif hasattr(res, "embedding") and res.embedding:
                    embeddings_list.append(res.embedding.values)
            arr = np.array(embeddings_list, dtype=np.float32)
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            return arr / norms

        if getattr(self, "_backend", "") == "sentence_transformers":
            embeddings = self._model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return np.array(embeddings, dtype=np.float32)

        # FlagEmbedding backend
        output = self._model.encode(  # type: ignore[union-attr]
            texts,
            batch_size=batch_size,
            max_length=512,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        embeddings = np.array(output["dense_vecs"], dtype=np.float32)
        # L2 normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms


class DenseIndex:
    """Manages dense vector storage and retrieval via ChromaDB."""

    def __init__(
        self,
        persist_dir: str | Path,
        collection_name: str,
        embedding_model_name: str = "BAAI/bge-m3",
    ) -> None:
        self.persist_dir = str(Path(persist_dir).resolve())
        self.collection_name = collection_name
        self._embedder = EmbeddingModel(embedding_model_name)
        self._client = None
        self._collection = None

    def _init_chroma(self) -> None:
        if self._client is not None:
            return
        import chromadb  # type: ignore
        from chromadb.config import Settings as ChromaSettings

        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB ready: collection '%s' (%d vectors)",
            self.collection_name,
            self._collection.count(),
        )

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: list[DocumentChunk], batch_size: int = 64) -> None:
        """Embed and store a list of DocumentChunk objects in ChromaDB."""
        self._init_chroma()
        if not chunks:
            return

        # Filter out chunks already in the collection
        existing_ids = set(
            self._collection.get(ids=[c.chunk_id for c in chunks])["ids"]  # type: ignore[index]
        )
        new_chunks = [c for c in chunks if c.chunk_id not in existing_ids]
        if not new_chunks:
            logger.info("Dense: all %d chunks already indexed.", len(chunks))
            return

        logger.info("Dense: embedding %d new chunks...", len(new_chunks))
        texts = [c.text for c in new_chunks]

        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i : i + batch_size]
            batch_texts = texts[i : i + batch_size]
            embeddings = self._embedder.encode(batch_texts)

            self._collection.add(  # type: ignore[union-attr]
                ids=[c.chunk_id for c in batch],
                embeddings=embeddings.tolist(),
                documents=batch_texts,
                metadatas=[c.to_metadata_dict() for c in batch],
            )

        logger.info("Dense: indexed %d chunks.", len(new_chunks))

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 20,
        category_filter: Optional[str] = None,
    ) -> list[tuple[dict, float]]:
        """
        Retrieve the top-k most similar chunks.

        Returns: list of (metadata_dict, similarity_score) tuples.
        Similarity is in [0, 1] (cosine).
        """
        self._init_chroma()

        query_emb = self._embedder.encode([query])
        where_filter = {"category": category_filter} if category_filter else None

        results = self._collection.query(  # type: ignore[union-attr]
            query_embeddings=query_emb.tolist(),
            n_results=min(top_k, max(1, self._collection.count())),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        hits: list[tuple[dict, float]] = []
        ids_list = results.get("ids", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        documents = results.get("documents", [[]])[0]

        for meta, dist, doc_text in zip(metadatas, distances, documents):
            # ChromaDB cosine distance → similarity: sim = 1 - dist
            similarity = float(1.0 - dist)
            meta_with_text = dict(meta)
            meta_with_text["text"] = doc_text
            hits.append((meta_with_text, similarity))

        return sorted(hits, key=lambda x: x[1], reverse=True)

    @property
    def is_ready(self) -> bool:
        try:
            self._init_chroma()
            return self._collection.count() > 0  # type: ignore[union-attr]
        except Exception:
            return False

    @property
    def vector_count(self) -> int:
        try:
            self._init_chroma()
            return self._collection.count()  # type: ignore[union-attr]
        except Exception:
            return 0

