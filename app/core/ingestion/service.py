"""Orchestrate ingestion: read from storage, parse, chunk, embed, store in vector DB."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.ingestion.chunker import Chunk, TextChunker
from app.core.ingestion.parser import DocumentParser, ParsedDocument

if TYPE_CHECKING:
    from app.db.vector.base import VectorStore
    from app.providers.embeddings.base import EmbeddingProvider
    from app.providers.storage.base import StorageProvider


class IngestionService:
    """Orchestrates the full pipeline: read -> parse -> chunk -> embed -> store."""

    def __init__(
        self,
        storage: "StorageProvider",
        parser: DocumentParser,
        chunker: TextChunker,
        embedder: "EmbeddingProvider",
        vector_store: "VectorStore",
        batch_size: int = 64,
    ) -> None:
        self._storage = storage
        self._parser = parser
        self._chunker = chunker
        self._embedder = embedder
        self._vector_store = vector_store
        self._batch_size = batch_size

    async def ingest(self, key: str) -> int:
        """Ingest a document by key. Returns the number of chunks stored.

        Idempotent: re-running with the same key replaces existing vectors.
        """
        # 1. Read file bytes from storage
        data = await self._storage.get(key)

        # 2. Parse into ParsedDocument
        doc = self._parser.parse(key, data)

        # 3. Chunk into list[Chunk]
        chunks = self._chunker.chunk(doc, key)
        if not chunks:
            return 0

        # 4. Batch embed: collect all embeddings in memory before storing
        all_embeddings: list[list[float]] = []
        for i in range(0, len(chunks), self._batch_size):
            batch = chunks[i : i + self._batch_size]
            texts = [c.text for c in batch]
            batch_embeddings = await self._embedder.embed(texts)
            all_embeddings.extend(batch_embeddings)

        # 5. Delete existing vectors for this source_key (idempotency)
        await self._vector_store.delete_by_source_key(key)

        # 6. Ensure table exists, then bulk add
        await self._vector_store.ensure_collection()
        documents = [c.text for c in chunks]
        metadatas = [c.to_metadata() for c in chunks]
        await self._vector_store.add_documents(
            documents=documents,
            embeddings=all_embeddings,
            metadatas=metadatas,
        )

        # 7. Ensure HNSW index exists
        await self._vector_store.ensure_index()

        return len(chunks)
