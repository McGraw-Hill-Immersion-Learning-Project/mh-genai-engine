"""FastAPI dependencies: settings, RAG retriever, LLM (override-friendly in tests)."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.config import Settings
from app.core.rag.retriever import Retriever
from app.providers import get_embedding_provider, get_llm_provider, get_vector_store
from app.providers.llm.base import LLMProvider


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process (env + .env)."""
    return Settings()


def get_retriever(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Retriever:
    """Embed queries and search the configured vector store."""
    return Retriever(
        get_embedding_provider(settings),
        get_vector_store(settings),
    )


def get_llm(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LLMProvider:
    """LLM used for lesson-outline generation."""
    return get_llm_provider(settings)
