"""
app/config.py — Central configuration via environment variables.
All settings are loaded once at startup via pydantic-settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = Field("development", description="Environment: development | production")
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Google Gemini
    gemini_api_key: str = Field(..., description="Google Gemini API key (required)")

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma_db"
    chroma_collection_name: str = "citizen_services"

    # BM25
    bm25_index_path: str = "./data/bm25_index.pkl"

    # Metadata DB (SQLite)
    metadata_db_path: str = "./data/metadata.db"

    # Retrieval
    bm25_top_k: int = 20
    dense_top_k: int = 20
    reranker_top_k: int = 5
    evidence_threshold: float = Field(0.40, ge=0.0, le=1.0)

    # LLM
    generation_model: str = "gemini-3.1-flash-lite"
    generation_max_tokens: int = 2048
    generation_temperature: float = Field(0.1, ge=0.0, le=2.0)

    # Embedding / Reranker
    embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    # Rate limiting
    rate_limit_requests: int = 20
    rate_limit_period: int = 60

    # Frontend
    backend_url: str = "http://localhost:8000"
    streamlit_port: int = 8501

    @field_validator("chroma_persist_dir", "bm25_index_path", "metadata_db_path", mode="before")
    @classmethod
    def _resolve_path(cls, v: str) -> str:
        return str(Path(v).resolve())

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

