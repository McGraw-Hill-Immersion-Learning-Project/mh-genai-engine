"""pgvector adapter tests. Require Docker Postgres with pgvector."""

import os
from collections.abc import AsyncIterator

import asyncpg
import pytest

from app.db.vector.filters import VectorMetadataFilter
from app.db.vector.pgvector import PgvectorStore

# Skip entire module if DATABASE_URL not set (e.g. CI without Docker)
pytestmark = [
    pytest.mark.pgvector,
    pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="DATABASE_URL not set; run: docker compose up db",
    ),
]


@pytest.fixture
def db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    return url


@pytest.fixture
async def pgvector_store(db_url: str) -> AsyncIterator[PgvectorStore]:
    """PgvectorStore with unique table per test, cleaned up after."""
    import uuid

    table_name = f"chunks_test_{uuid.uuid4().hex[:8]}"
    store = PgvectorStore(
        database_url=db_url,
        table_name=table_name,
        dimensions=8,
    )
    try:
        yield store
    finally:
        # Best-effort cleanup so the dev DB doesn't accumulate test tables.
        conn = await asyncpg.connect(db_url)
        try:
            await conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        finally:
            await conn.close()


@pytest.mark.asyncio
async def test_ensure_collection_idempotent(pgvector_store: PgvectorStore) -> None:
    """ensure_collection creates table and can be called multiple times."""
    await pgvector_store.ensure_collection()
    await pgvector_store.ensure_collection()


@pytest.mark.asyncio
async def test_add_documents_and_query(
    pgvector_store: PgvectorStore,
) -> None:
    """add_documents stores and query returns results sorted by similarity."""
    await pgvector_store.ensure_collection()
    docs = ["First chunk", "Second chunk", "Third chunk"]
    embeddings = [[1.0] * 8, [0.5] * 8, [0.0] * 8]
    metadatas = [
        {"source_key": "test.pdf", "chunk_id": 0},
        {"source_key": "test.pdf", "chunk_id": 1},
        {"source_key": "test.pdf", "chunk_id": 2},
    ]
    ids = await pgvector_store.add_documents(docs, embeddings, metadatas)
    assert len(ids) == 3
    assert ids[0] == "test.pdf_0"

    results = await pgvector_store.query([1.0] * 8, n_results=2)
    assert len(results) == 2
    assert results[0]["content"] == "First chunk"
    assert results[0]["metadata"]["chunk_id"] == 0


@pytest.mark.asyncio
async def test_query_with_metadata_filter_chapter(
    pgvector_store: PgvectorStore,
) -> None:
    """SQL WHERE metadata filters restrict rows before ORDER BY distance."""
    await pgvector_store.ensure_collection()
    docs = ["Ch1 chunk", "Ch2 chunk", "Ch1 other"]
    embeddings = [[1.0] * 8, [0.99] * 8, [0.5] * 8]
    metadatas = [
        {
            "source_key": "t.pdf",
            "chunk_id": 0,
            "chapter": "1",
            "section": "1.1",
            "title": "Algebra",
        },
        {
            "source_key": "t.pdf",
            "chunk_id": 1,
            "chapter": "2",
            "section": "2.1",
            "title": "Algebra",
        },
        {
            "source_key": "t.pdf",
            "chunk_id": 2,
            "chapter": "1",
            "section": "1.2",
            "title": "Geometry",
        },
    ]
    await pgvector_store.add_documents(docs, embeddings, metadatas)
    flt = VectorMetadataFilter(chapter="1")
    results = await pgvector_store.query(
        [1.0] * 8, n_results=10, metadata_filter=flt
    )
    assert len(results) == 2
    assert {r["metadata"]["section"] for r in results} == {"1.1", "1.2"}
    assert results[0]["content"] == "Ch1 chunk"


@pytest.mark.asyncio
async def test_query_metadata_filter_book_substring_in_title(
    pgvector_store: PgvectorStore,
) -> None:
    await pgvector_store.ensure_collection()
    docs = ["A", "B"]
    embeddings = [[1.0] * 8, [1.0] * 8]
    metadatas = [
        {"source_key": "a", "chunk_id": 0, "chapter": "1", "title": "Intro Physics"},
        {"source_key": "a", "chunk_id": 1, "chapter": "1", "title": "Chemistry Basics"},
    ]
    await pgvector_store.add_documents(docs, embeddings, metadatas)
    results = await pgvector_store.query(
        [1.0] * 8,
        n_results=10,
        metadata_filter=VectorMetadataFilter(chapter="1", book="physics"),
    )
    assert len(results) == 1
    assert results[0]["content"] == "A"


@pytest.mark.asyncio
async def test_delete_by_source_key(pgvector_store: PgvectorStore) -> None:
    """delete_by_source_key removes only matching documents."""
    await pgvector_store.ensure_collection()
    docs = ["A", "B"]
    embeddings = [[0.0] * 8, [0.0] * 8]
    metadatas = [
        {"source_key": "doc1.pdf", "chunk_id": 0},
        {"source_key": "doc2.pdf", "chunk_id": 0},
    ]
    await pgvector_store.add_documents(docs, embeddings, metadatas)
    await pgvector_store.delete_by_source_key("doc1.pdf")

    results = await pgvector_store.query([0.0] * 8, n_results=10)
    assert len(results) == 1
    assert results[0]["metadata"]["source_key"] == "doc2.pdf"


@pytest.mark.asyncio
async def test_ensure_index_idempotent(pgvector_store: PgvectorStore) -> None:
    """ensure_index creates HNSW index and can be called multiple times."""
    await pgvector_store.ensure_collection()
    await pgvector_store.add_documents(
        ["x"],
        [[0.0] * 8],
        [{"source_key": "x", "chunk_id": 0}],
    )
    await pgvector_store.ensure_index()
    await pgvector_store.ensure_index()
