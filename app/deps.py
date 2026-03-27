"""FastAPI dependencies: settings, RAG retriever, LLM (override-friendly in tests)."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.config import Settings
from app.core.rag.retriever import Retriever
from app.providers import get_embedding_provider, get_llm_provider, get_storage_provider, get_vector_store
from app.providers.llm.base import LLMProvider
from app.providers.storage.base import StorageProvider


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


def get_storage(
    settings: Annotated[Settings, Depends(get_settings)],
) -> StorageProvider:
    """Storage backend used to persist uploaded documents."""
    return get_storage_provider(settings)


def get_ingestion_service(
    settings: Annotated[Settings, Depends(get_settings)],
):
    """Fully configured ingestion pipeline for uploaded documents."""
    from app.core.ingestion.chunker import TextChunker
    from app.core.ingestion.parser import DocumentParser
    from app.core.ingestion.service import IngestionService

    return IngestionService(
        storage=get_storage_provider(settings),
        parser=DocumentParser(
            do_ocr=settings.do_ocr,
            do_table_structure=settings.do_table_structure,
            ocr_batch_size=settings.docling_ocr_batch_size,
            layout_batch_size=settings.docling_layout_batch_size,
            table_batch_size=settings.docling_table_batch_size,
            queue_max_size=settings.docling_queue_max_size,
        ),
        chunker=TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        ),
        embedder=get_embedding_provider(settings),
        vector_store=get_vector_store(settings),
        batch_size=settings.embedding_batch_size,
        batch_delay_seconds=settings.embedding_batch_delay_seconds,
        max_chunks=settings.dev_max_chunks,
    )
