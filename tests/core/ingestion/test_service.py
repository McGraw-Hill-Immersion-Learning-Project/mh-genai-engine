"""Ingestion service integration tests."""

import pytest

from app.core.ingestion.chunker import TextChunker
from app.core.ingestion.parser import DocumentParser
from app.core.ingestion.service import IngestionService


@pytest.mark.asyncio
async def test_ingest_full_pipeline(
    fake_storage,
    fake_embedder,
    in_memory_store,
) -> None:
    """Full pipeline: PDF in -> chunks with embeddings stored."""
    parser = DocumentParser()
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    service = IngestionService(
        storage=fake_storage,
        parser=parser,
        chunker=chunker,
        embedder=fake_embedder,
        vector_store=in_memory_store,
        batch_size=64,
    )

    count = await service.ingest("sample.pdf")

    # 1. Correct number of chunks stored
    assert count == len(in_memory_store.documents)
    assert count > 0

    # 2. All metadata fields present and correct
    required_fields = {"source_key", "title", "page_number", "chapter", "section", "chunk_id"}
    for meta in in_memory_store.metadatas:
        assert required_fields.issubset(meta.keys())
        assert meta["source_key"] == "sample.pdf"

    # 3. Embedding dimensions match
    assert all(len(emb) == 8 for emb in in_memory_store.embeddings)

    # 4. source_key matches input
    assert all(m.get("source_key") == "sample.pdf" for m in in_memory_store.metadatas)


@pytest.mark.asyncio
async def test_ingest_idempotent(
    fake_storage,
    fake_embedder,
    in_memory_store,
) -> None:
    """Re-running ingest produces same count, not doubled."""
    parser = DocumentParser()
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    service = IngestionService(
        storage=fake_storage,
        parser=parser,
        chunker=chunker,
        embedder=fake_embedder,
        vector_store=in_memory_store,
        batch_size=64,
    )

    count1 = await service.ingest("sample.pdf")
    count2 = await service.ingest("sample.pdf")

    assert count1 == count2
    assert len(in_memory_store.documents) == count1
