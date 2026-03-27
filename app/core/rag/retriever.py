"""Query vector store and assemble context window for the generator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.db.vector.filters import VectorMetadataFilter
from app.utils import get_logger

logger = get_logger(__name__)

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
        chunks = [
            RetrievedChunk(content=row["content"], metadata=dict(row.get("metadata") or {}))
            for row in rows
        ]
        logger.info(
            "vector_retrieve_done n_results_requested=%d n_chunks=%d query_len=%d "
            "metadata_filter=%r",
            n_results,
            len(chunks),
            len(query),
            metadata_filter,
        )
        for i, ch in enumerate(chunks):
            meta = ch.metadata
            preview = (ch.content[:160] + "…") if len(ch.content) > 160 else ch.content
            logger.debug(
                "vector_retrieve_chunk i=%d source_key=%r page_number=%s "
                "content_len=%d preview=%r",
                i,
                meta.get("source_key"),
                meta.get("page_number"),
                len(ch.content),
                preview.replace("\n", " "),
            )
        logger.debug("vector_retrieve_query=%r", query)
        return chunks

    async def retrieve_by_ids(self, ids: list[str]) -> list[RetrievedChunk]:
        """Load chunks by primary key (no embedding). Order matches *ids* for found rows."""
        rows = await self._vector_store.get_by_ids(ids)
        chunks = [
            RetrievedChunk(content=row["content"], metadata=dict(row.get("metadata") or {}))
            for row in rows
        ]
        logger.info(
            "vector_retrieve_by_ids requested=%d n_chunks=%d",
            len(ids),
            len(chunks),
        )
        return chunks
