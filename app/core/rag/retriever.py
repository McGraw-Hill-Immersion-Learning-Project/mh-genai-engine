"""Query vector store and assemble context window for the generator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.db.vector.filters import VectorMetadataFilter

if TYPE_CHECKING:
    from app.db.vector.base import VectorStore
    from app.providers.embeddings.base import EmbeddingProvider


@dataclass(frozen=True)
class RetrievedChunk:
    """One chunk from the vector store with provenance metadata."""

    content: str
    metadata: dict

    # Expected metadata keys (from ingestion chunker): source_key, title,
    # page_number, chapter, section, chunk_id


class Retriever:
    """Embed a query and retrieve similar chunks from the vector store."""

    def __init__(
        self,
        embedder: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._embedder = embedder
        self._vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        n_results: int = 10,
        *,
        metadata_filter: VectorMetadataFilter | None = None,
    ) -> list[RetrievedChunk]:
        """Embed *query*, search the vector store, return chunks with metadata."""
        vectors = await self._embedder.embed([query])
        if not vectors:
            return []
        embedding = vectors[0]
        rows = await self._vector_store.query(
            embedding,
            n_results=n_results,
            metadata_filter=metadata_filter,
        )
        return [
            RetrievedChunk(content=row["content"], metadata=dict(row.get("metadata") or {}))
            for row in rows
        ]
