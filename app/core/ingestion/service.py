"""Orchestrate ingestion: read from storage, parse, chunk, embed, store in vector DB."""

import logging

from app.core.ingestion.chunker import TextChunker
from app.core.ingestion.parser import DocumentParser
from app.providers.embeddings.base import EmbeddingProvider
from app.providers.storage.base import StorageProvider
from app.db.vector.base import VectorStore

logger = logging.getLogger(__name__)


class IngestionService:
    """Wires storage → parser → chunker → embedder → vector store."""

    def __init__(
        self,
        storage: StorageProvider,
        embedder: EmbeddingProvider,
        vector_store: VectorStore,
    ):
        self._storage = storage
        self._embedder = embedder
        self._vector_store = vector_store
        self._parser = DocumentParser()
        self._chunker = TextChunker()

    async def ingest(self, key: str) -> int:
        """Ingest a single document by storage key. Returns number of chunks stored."""
        logger.info("Ingesting %s", key)

        data = await self._storage.get(key)
        text = self._parser.parse(key, data)
        chunks = self._chunker.chunk(text, source=key)

        if not chunks:
            logger.warning("No chunks produced for %s", key)
            return 0

        texts = [c.text for c in chunks]
        embeddings = await self._embedder.embed(texts, input_type="document")
        metadatas = [{"source": c.source, "index": c.index} for c in chunks]

        await self._vector_store.add_documents(texts, embeddings, metadatas)
        logger.info("Stored %d chunks for %s", len(chunks), key)
        return len(chunks)

    async def ingest_all(self, prefix: str = "") -> dict[str, int]:
        """Ingest all files in storage matching prefix. Returns {key: chunk_count}."""
        keys = await self._storage.list_files(prefix)
        results = {}
        for key in keys:
            results[key] = await self.ingest(key)
        return results