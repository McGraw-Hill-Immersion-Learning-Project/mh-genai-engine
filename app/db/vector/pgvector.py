"""pgvector vector store using asyncpg."""

import json
import re

import asyncpg

from app.db.vector.base import VectorStore


def _vector_to_str(embedding: list[float]) -> str:
    """Format embedding list as PostgreSQL vector literal."""
    return "[" + ",".join(str(x) for x in embedding) + "]"


def _validate_table_name(name: str) -> None:
    """Raise ValueError if table name is not a safe identifier."""
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise ValueError(
            f"Invalid table name {name!r}. Use alphanumeric and underscores only."
        )


class PgvectorStore:
    """pgvector-backed vector store with HNSW cosine index."""

    def __init__(
        self,
        database_url: str,
        table_name: str = "chunks",
        dimensions: int = 1024,
    ) -> None:
        _validate_table_name(table_name)
        self._database_url = database_url
        self._table_name = table_name
        self._dimensions = dimensions

    async def ensure_collection(self) -> None:
        """Create table and enable vector extension if they do not exist."""
        conn = await asyncpg.connect(self._database_url)
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding vector({self._dimensions}),
                    metadata JSONB
                )
                """
            )
        finally:
            await conn.close()

    async def ensure_index(self) -> None:
        """Create HNSW cosine index if it does not exist."""
        index_name = f"{self._table_name}_embedding_hnsw_idx"
        conn = await asyncpg.connect(self._database_url)
        try:
            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {self._table_name}
                USING hnsw (embedding vector_cosine_ops)
                """
            )
        finally:
            await conn.close()

    async def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> list[str]:
        """Add documents with embeddings. Return list of document IDs."""
        if metadatas is None:
            metadatas = [{}] * len(documents)
        if len(documents) != len(embeddings) or len(documents) != len(metadatas):
            raise ValueError(
                "documents, embeddings, and metadatas must have the same length"
            )

        ids: list[str] = []
        for i, meta in enumerate(metadatas):
            source_key = meta.get("source_key", "")
            chunk_id = meta.get("chunk_id", i)
            doc_id = f"{source_key}_{chunk_id}"
            ids.append(doc_id)

        conn = await asyncpg.connect(self._database_url)
        try:
            for i, (doc, emb, meta, doc_id) in enumerate(
                zip(documents, embeddings, metadatas, ids)
            ):
                vector_str = _vector_to_str(emb)
                await conn.execute(
                    f"""
                    INSERT INTO {self._table_name} (id, content, embedding, metadata)
                    VALUES ($1, $2, $3::vector, $4::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                    """,
                    doc_id,
                    doc,
                    vector_str,
                    json.dumps(meta),
                )
        finally:
            await conn.close()

        return ids

    async def query(
        self,
        embedding: list[float],
        n_results: int = 10,
    ) -> list[dict]:
        """Query by embedding vector. Return list of matches with metadata."""
        vector_str = _vector_to_str(embedding)
        conn = await asyncpg.connect(self._database_url)
        try:
            rows = await conn.fetch(
                f"""
                SELECT id, content, metadata,
                       embedding <=> $1::vector AS distance
                FROM {self._table_name}
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                vector_str,
                n_results,
            )
        finally:
            await conn.close()

        def _normalize_metadata(raw: str | dict | None) -> dict:
            if raw is None:
                return {}
            if isinstance(raw, str):
                return json.loads(raw) if raw else {}
            return raw if isinstance(raw, dict) else {}

        return [
            {
                "id": row["id"],
                "content": row["content"],
                "metadata": _normalize_metadata(row["metadata"]),
                "distance": float(row["distance"]),
            }
            for row in rows
        ]

    async def delete(self, ids: list[str]) -> None:
        """Delete documents by ID."""
        if not ids:
            return
        conn = await asyncpg.connect(self._database_url)
        try:
            await conn.execute(
                f"DELETE FROM {self._table_name} WHERE id = ANY($1::text[])",
                ids,
            )
        finally:
            await conn.close()

    async def delete_by_source_key(self, source_key: str) -> None:
        """Delete all documents with the given source_key (for idempotency)."""
        conn = await asyncpg.connect(self._database_url)
        try:
            await conn.execute(
                f"""
                DELETE FROM {self._table_name}
                WHERE metadata->>'source_key' = $1
                """,
                source_key,
            )
        finally:
            await conn.close()
