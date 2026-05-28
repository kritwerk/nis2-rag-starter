"""Configuration via environment variables / .env."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for nis2-rag.

    Defaults work offline: local sentence-transformer for embeddings,
    Ollama-compatible endpoint for the LLM. Set OPENAI_API_KEY (and switch
    the model name) to use OpenAI instead.
    """

    model_config = SettingsConfigDict(
        env_prefix="NIS2_RAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Storage
    chroma_dir: Path = Field(default=Path("./chroma"))
    collection_name: str = Field(default="nis2_policies")

    # Chunking
    chunk_size: int = Field(default=800, ge=100, le=4000)
    chunk_overlap: int = Field(default=100, ge=0, le=1000)

    # Embeddings (local by default — no API key required)
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")

    # LLM
    llm_provider: str = Field(default="openai")  # "openai" | "ollama" | "echo"
    llm_model: str = Field(default="gpt-4o-mini")
    llm_base_url: str | None = Field(default=None)  # set to http://localhost:11434/v1 for ollama
    llm_api_key: str = Field(default="not-set")
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)

    # Retrieval
    top_k: int = Field(default=5, ge=1, le=20)


def load_settings() -> Settings:
    """Load settings; isolated for easy test override."""
    return Settings()
