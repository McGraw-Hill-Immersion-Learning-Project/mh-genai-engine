"""Orchestrate ingestion: read from storage, parse, chunk, embed, store in vector DB."""

import logging

from app.core.ingestion.chunker import TextChunker
from app.core.ingestion.parser import DocumentParser
from app.providers.embeddings.base import EmbeddingProvider
from app.providers.storage.base import StorageProvider
from app.db.vector.base import VectorStore

logger = logging.getLogger(__name__)


def _build_toc_index(toc: list) -> list[tuple[int, str, str]]:
    """Convert TOC into a sorted list of (page, chapter, section) tuples.

    TOC format from pymupdf: [[level, title, page], ...]
    Level 1 = chapter, Level 2 = section.
    """
    index = []
    current_chapter = ""
    for level, title, page in toc:
        if level == 1:
            current_chapter = title
            index.append((page, current_chapter, ""))
        elif level == 2:
            index.append((page, current_chapter, title))
    return sorted(index, key=lambda x: x[0])


def _lookup_toc(toc_index: list, page_number: int) -> tuple[str, str]:
    """Find the chapter and section for a given page number."""
    chapter, section = "", ""
    for page, chap, sec in toc_index:
        if page <= page_number:
            chapter, section = chap, sec
        else:
            break
    return chapter, section


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

    async def ingest(self, key: str, subject: str = "", book_id: str = "") -> int:
        """Ingest a single document by storage key. Returns number of chunks stored."""
        logger.info("Ingesting %s", key)

        data = await self._storage.get(key)
        doc = self._parser.parse(key, data)
        chunks = self._chunker.chunk(doc, source=key)

        if not chunks:
            logger.warning("No chunks produced for %s", key)
            return 0

        toc_index = _build_toc_index(doc.toc) if doc.toc else []

        texts = [c.text for c in chunks]
        embeddings = await self._embedder.embed(texts, input_type="document")

        metadatas = []
        for c in chunks:
            chapter, section = _lookup_toc(toc_index, c.page_number) if toc_index else ("", "")
            metadatas.append({
                "source": c.source,
                "index": c.index,
                "page_number": c.page_number,
                "title": doc.title,
                "subject": subject,
                "book_id": book_id,
                "chapter": chapter,
                "section": section,
            })

        await self._vector_store.add_documents(texts, embeddings, metadatas)
        logger.info("Stored %d chunks for %s", len(chunks), key)
        return len(chunks)

    async def ingest_all(self, prefix: str = "", subject: str = "", book_id: str = "") -> dict[str, int]:
        """Ingest all files in storage matching prefix. Returns {key: chunk_count}."""
        keys = await self._storage.list_files(prefix)
        results = {}
        for key in keys:
            results[key] = await self.ingest(key, subject=subject, book_id=book_id)
        return results
