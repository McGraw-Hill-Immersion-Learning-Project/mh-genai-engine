"""pgvector adapter tests. Require Docker Postgres with pgvector."""

import os

import pytest

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
def pgvector_store(db_url: str) -> PgvectorStore:
    """PgvectorStore with unique table per test to avoid collisions."""
    import uuid
    table_name = f"chunks_test_{uuid.uuid4().hex[:8]}"
    return PgvectorStore(
        database_url=db_url,
        table_name=table_name,
        dimensions=8,
    )


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
