"""pgvector vector store using asyncpg."""

import json
import re

import asyncpg

from app.db.vector.base import VectorStore
from app.db.vector.filters import VectorMetadataFilter
from app.db.vector.ids import chunk_document_id
from app.utils import make_pgvector_index_name


def _vector_to_str(embedding: list[float]) -> str:
    """Format embedding list as PostgreSQL vector literal."""
    return "[" + ",".join(str(x) for x in embedding) + "]"


def _escape_like_prefix(pattern: str) -> str:
    """Escape ``%``, ``_``, ``\\`` for use in ``LIKE pat || '%' ESCAPE '\\'``."""
    return (
        pattern.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )


def _validate_table_name(name: str) -> None:
    """Raise ValueError if table name is not a safe identifier."""
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise ValueError(
            f"Invalid table name {name!r}. Use alphanumeric and underscores only."
        )


def _normalize_metadata(raw: str | dict | None) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, str):
        return json.loads(raw) if raw else {}
    return raw if isinstance(raw, dict) else {}


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
        index_name = make_pgvector_index_name(
            table_name=self._table_name, suffix="embedding_hnsw_idx"
        )
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
            ids.append(chunk_document_id(meta, i))

        conn = await asyncpg.connect(self._database_url)
        try:
            for i, (doc, emb, meta, doc_id) in enumerate(
                zip(documents, embeddings, metadatas, ids)
            ):
                # Postgres TEXT cannot store NUL bytes; sanitize content to avoid
                # "invalid byte sequence for encoding \"UTF8\": 0x00" errors.
                clean_doc = doc.replace("\x00", " ")
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
                    clean_doc,
                    vector_str,
                    json.dumps(meta),
                )
        finally:
            await conn.close()

        return ids

    async def get_by_ids(self, ids: list[str]) -> list[dict]:
        """Return rows in the order of *ids*; skip ids not found."""
        if not ids:
            return []

        conn = await asyncpg.connect(self._database_url)
        try:
            rows = await conn.fetch(
                f"""
                SELECT id, content, metadata
                FROM {self._table_name}
                WHERE id = ANY($1::text[])
                """,
                ids,
            )
        finally:
            await conn.close()

        by_id = {row["id"]: row for row in rows}
        ordered: list[dict] = []
        for doc_id in ids:
            row = by_id.get(doc_id)
            if row is None:
                continue
            ordered.append(
                {
                    "id": row["id"],
                    "content": row["content"],
                    "metadata": _normalize_metadata(row["metadata"]),
                }
            )
        return ordered

    async def query(
        self,
        embedding: list[float],
        n_results: int = 10,
        *,
        metadata_filter: VectorMetadataFilter | None = None,
    ) -> list[dict]:
        """Query by embedding vector. Return list of matches with metadata."""
        vector_str = _vector_to_str(embedding)
        conn = await asyncpg.connect(self._database_url)
        try:
            where_parts: list[str] = ["TRUE"]
            bind_args: list[object] = [vector_str, n_results]
            i = 3

            if metadata_filter is not None and metadata_filter.has_any():
                if metadata_filter.chapter is not None and str(
                    metadata_filter.chapter
                ).strip():
                    where_parts.append(f"metadata->>'chapter' = ${i}")
                    bind_args.append(metadata_filter.chapter)
                    i += 1
                if metadata_filter.section is not None and str(
                    metadata_filter.section
                ).strip():
                    where_parts.append(f"metadata->>'section' = ${i}")
                    bind_args.append(metadata_filter.section)
                    i += 1
                if metadata_filter.sub_section is not None and str(
                    metadata_filter.sub_section
                ).strip():
                    esc = _escape_like_prefix(metadata_filter.sub_section)
                    where_parts.append(
                        f"(metadata->>'section' LIKE ${i} || '%' ESCAPE E'\\\\')"
                    )
                    bind_args.append(esc)
                    i += 1
                if metadata_filter.book is not None and str(
                    metadata_filter.book
                ).strip():
                    where_parts.append(
                        f"(POSITION(LOWER(${i}) IN LOWER(COALESCE(metadata->>'title', ''))) > 0 "
                        f"OR POSITION(LOWER(${i}) IN LOWER(COALESCE(metadata->>'source_key', ''))) > 0)"
                    )
                    bind_args.append(metadata_filter.book)
                    i += 1

            where_sql = " AND ".join(where_parts)
            sql = f"""
                SELECT id, content, metadata,
                       embedding <=> $1::vector AS distance
                FROM {self._table_name}
                WHERE {where_sql}
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """
            rows = await conn.fetch(sql, *bind_args)
        finally:
            await conn.close()

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
