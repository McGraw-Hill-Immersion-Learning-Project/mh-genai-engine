"""pgvector vector store using asyncpg."""

import uuid
import asyncpg
from pgvector.asyncpg import register_vector

from app.config import settings

VECTOR_DIM = 768  # bge-base-en-v1.5 output dimension


class PGVectorStore:
    """Store and query document embeddings in PostgreSQL using pgvector."""

    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def initialize(self) -> None:
        """Create connection pool, enable pgvector extension, and create table + index."""
        self._pool = await asyncpg.create_pool(settings.database_url, init=register_vector)
        async with self._pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    text        TEXT NOT NULL,
                    embedding   VECTOR(768),
                    metadata    JSONB DEFAULT '{}'
                )
            """)
            # HNSW index for fast approximate nearest-neighbour search
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
                ON document_chunks
                USING hnsw (embedding vector_cosine_ops)
            """)

    async def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> list[str]:
        """Insert chunks with embeddings. Returns list of inserted UUIDs."""
        metadatas = metadatas or [{} for _ in documents]
        ids = [str(uuid.uuid4()) for _ in documents]

        rows = [
            (ids[i], documents[i], embeddings[i], metadatas[i])
            for i in range(len(documents))
        ]

        async with self._pool.acquire() as conn:
            await conn.executemany(
                "INSERT INTO document_chunks (id, text, embedding, metadata) VALUES ($1, $2, $3, $4)",
                rows,
            )
        return ids

    async def query(
        self,
        embedding: list[float],
        n_results: int = 10,
    ) -> list[dict]:
        """Return top-n chunks by cosine similarity."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, text, metadata,
                       1 - (embedding <=> $1::vector) AS score
                FROM document_chunks
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                embedding,
                n_results,
            )
        return [
            {"id": str(r["id"]), "text": r["text"], "metadata": r["metadata"], "score": r["score"]}
            for r in rows
        ]

    async def delete(self, ids: list[str]) -> None:
        """Delete chunks by UUID."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM document_chunks WHERE id = ANY($1::uuid[])",
                ids,
            )