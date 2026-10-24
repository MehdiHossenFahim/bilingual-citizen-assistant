"""
app/main.py — FastAPI application entry point.

Startup sequence:
  1. Load settings from environment
  2. Load BM25 index from disk
  3. Initialise ChromaDB dense index
  4. Load cross-encoder reranker
  5. Initialise Gemini answer generator
  6. Inject dependencies into LangGraph nodes
  7. Build and attach RAG workflow
"""

from __future__ import annotations

import logging
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat as chat_router
from app.api.routes import sources as sources_router
from app.api.routes import feedback as feedback_router
from app.api.schemas import ErrorResponse, HealthResponse, ReadinessResponse
from app.config import get_settings

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise all heavyweight resources once at startup."""
    settings = get_settings()
    logger.info("Starting Bilingual Citizen Services AI Assistant…")

    # ---- BM25 ----
    from app.retrieval.bm25 import BM25Index
    bm25 = BM25Index(settings.bm25_index_path)
    bm25.load()
    app.state.bm25_index = bm25

    # ---- Dense / ChromaDB ----
    from app.retrieval.dense_search import DenseIndex
    dense = DenseIndex(
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name,
        embedding_model_name=settings.embedding_model,
    )
    app.state.dense_index = dense

    # ---- Reranker ----
    from app.retrieval.reranker import CrossEncoderReranker
    reranker = CrossEncoderReranker(settings.reranker_model)
    app.state.reranker = reranker

    # ---- Generator ----
    from app.generation.generator import AnswerGenerator
    generator = AnswerGenerator(
        api_key=settings.gemini_api_key,
        model=settings.generation_model,
        max_tokens=settings.generation_max_tokens,
        temperature=settings.generation_temperature,
    )
    app.state.generator = generator

    # ---- Inject into LangGraph nodes ----
    from app.graph.nodes import set_dependencies
    set_dependencies(bm25, dense, reranker, generator)

    # ---- Build workflow ----
    from app.graph.workflow import RAGWorkflow
    app.state.workflow = RAGWorkflow()

    # ---- Non-blocking background auto-ingestion ----
    # Runs asynchronously in a worker thread so Uvicorn can immediately bind the port
    # and satisfy cloud health checks / port scanners (e.g. Render) in < 1 second.
    if not bm25.is_ready or not dense.is_ready:
        import asyncio
        from pathlib import Path

        async def _background_ingest():
            sample_path = Path(__file__).parent.parent / "data" / "sources" / "sample_data.json"
            if sample_path.exists():
                logger.info("Empty index detected. Ingesting official citizen services sample data in background...")
                try:
                    from app.ingestion.loaders import JSONFAQLoader
                    from scripts.ingest import run_ingestion
                    loader = JSONFAQLoader()
                    docs = loader.load_file(sample_path)
                    await asyncio.to_thread(run_ingestion, docs, settings)
                    bm25.load()
                    logger.info("Background auto-ingestion completed successfully. Knowledge base is ready.")
                except Exception as e:
                    logger.warning("Background auto-ingestion skipped or failed: %s", e)

        asyncio.create_task(_background_ingest())

    logger.info("All components initialised. Server listening and ready.")

    yield  # Application runs here and port is immediately available!

    logger.info("Shutting down…")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Bilingual Citizen Services AI Assistant",
        description=(
            "RAG-powered assistant for Bangladesh government services. "
            "Supports Bangla and English queries with grounded, cited answers."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS (Permit Vercel frontend, local dev, and public clients)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Rate Limiting (protect LLM / compute resources)
    from app.api.rate_limiter import RateLimitMiddleware
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_period,
    )

    # ---- Routers ----
    app.include_router(chat_router.router, prefix="/api/v1", tags=["Chat"])
    app.include_router(sources_router.router, prefix="/api/v1", tags=["Sources"])
    app.include_router(feedback_router.router, prefix="/api/v1", tags=["Feedback"])

    # ---- Health endpoints ----
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health() -> HealthResponse:
        return HealthResponse()

    @app.get("/ready", response_model=ReadinessResponse, tags=["Health"])
    async def ready(request: Request) -> ReadinessResponse:
        checks: dict[str, str] = {}

        bm25 = getattr(request.app.state, "bm25_index", None)
        checks["bm25_index"] = "ok" if (bm25 and bm25.is_ready) else "not_ready"

        dense = getattr(request.app.state, "dense_index", None)
        checks["dense_index"] = "ok" if (dense and dense.is_ready) else "not_ready"

        workflow = getattr(request.app.state, "workflow", None)
        checks["workflow"] = "ok" if workflow is not None else "not_ready"

        all_ready = all(v == "ok" for v in checks.values())

        return ReadinessResponse(ready=all_ready, checks=checks)

    # ---- Global error handler ----
    @app.exception_handler(Exception)
    async def _global_handler(request: Request, exc: Exception):
        logger.error("Unhandled error on %s: %s", request.url, exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "details": [],
            },
        )

    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )

