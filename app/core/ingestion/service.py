"""Orchestrate ingestion: read from storage, parse, chunk, embed, store in vector DB."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from app.core.ingestion.chunker import Chunk, TextChunker
from app.core.ingestion.parser import DocumentParser, ParsedDocument
from utils import get_logger

logger = get_logger(__name__)


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
        batch_delay_seconds: float = 0,
        max_chunks: int = 0,
    ) -> None:
        self._storage = storage
        self._parser = parser
        self._chunker = chunker
        self._embedder = embedder
        self._vector_store = vector_store
        self._batch_size = batch_size
        self._batch_delay_seconds = batch_delay_seconds
        self._max_chunks = max_chunks

    async def ingest(self, key: str) -> int:
        """Ingest a document by key. Returns the number of chunks stored.

        Idempotent: re-running with the same key replaces existing vectors.
        """
        logger.info("[ingest] Step 1: reading %r from storage...", key)
        # 1. Read file bytes from storage
        data = await self._storage.get(key)
        logger.info("[ingest] Step 1 complete: bytes loaded.")

        # 2. Parse into ParsedDocument
        logger.info("[ingest] Step 2: parsing document...")
        doc = self._parser.parse(key, data)
        logger.info(
            "[ingest] Step 2 complete: parsed document with %d pages.",
            len(doc.pages),
        )

        # 3. Chunk into list[Chunk]
        logger.info("[ingest] Step 3: chunking document...")
        chunks = self._chunker.chunk(doc, key)
        if not chunks:
            logger.info("[ingest] No chunks produced; nothing to store.")
            return 0
        if self._max_chunks and len(chunks) > self._max_chunks:
            logger.info(
                "[ingest] Step 3 note: capping chunks to %d (from %d).",
                self._max_chunks,
                len(chunks),
            )
            chunks = chunks[: self._max_chunks]
        logger.info(
            "[ingest] Step 3 complete: produced %d chunks.", len(chunks)
        )

        # 4. Batch embed: collect all embeddings in memory before storing
        logger.info(
            "[ingest] Step 4: embedding chunks (batch_size=%d)...",
            self._batch_size,
        )
        all_embeddings: list[list[float]] = []
        for i in range(0, len(chunks), self._batch_size):
            if i > 0 and self._batch_delay_seconds > 0:
                await asyncio.sleep(self._batch_delay_seconds)
            batch = chunks[i : i + self._batch_size]
            texts = [c.text for c in batch]
            batch_embeddings = await self._embedder.embed(texts)
            all_embeddings.extend(batch_embeddings)
            logger.info(
                "[ingest]   embedded batch %d (%d chunks).",
                i // self._batch_size + 1,
                len(batch),
            )
        logger.info(
            "[ingest] Step 4 complete: embedded %d chunks.",
            len(all_embeddings),
        )

        # 5. Ensure table exists (important for new embedding config tables)
        logger.info("[ingest] Step 5: ensuring collection...")
        await self._vector_store.ensure_collection()
        logger.info("[ingest] Step 5 complete: collection ensured.")

        # 6. Delete existing vectors for this source_key (idempotency)
        logger.info("[ingest] Step 6: deleting existing vectors for this source...")
        await self._vector_store.delete_by_source_key(key)
        logger.info("[ingest] Step 6 complete.")

        # 7. Bulk add
        logger.info("[ingest] Step 7: adding documents...")
        documents = [c.text for c in chunks]
        metadatas = [c.to_metadata() for c in chunks]
        await self._vector_store.add_documents(
            documents=documents,
            embeddings=all_embeddings,
            metadatas=metadatas,
        )
        logger.info("[ingest] Step 7 complete: documents added.")

        # 8. Ensure HNSW index exists
        logger.info("[ingest] Step 8: ensuring HNSW index...")
        await self._vector_store.ensure_index()
        logger.info("[ingest] Step 8 complete: index ensured.")

        return len(chunks)
