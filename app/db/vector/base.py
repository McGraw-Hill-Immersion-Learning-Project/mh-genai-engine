"""Vector store interface. Implementation: pgvector."""

from typing import Protocol

from app.db.vector.filters import VectorMetadataFilter


class VectorStore(Protocol):
    """Protocol for vector storage. Implementation: pgvector."""

    async def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> list[str]:
        """Add documents with embeddings. Return list of document IDs."""
        ...

    async def get_by_ids(self, ids: list[str]) -> list[dict]:
        """Fetch rows by primary key. Each dict has ``id``, ``content``, ``metadata`` (no ``distance``).

        Implementations should return rows in the same order as *ids* (omit missing ids).
        """
        ...

    async def query(
        self,
        embedding: list[float],
        n_results: int = 10,
        *,
        metadata_filter: VectorMetadataFilter | None = None,
    ) -> list[dict]:
        """Query by embedding vector. Return list of matches with metadata.

        When *metadata_filter* is set and ``has_any()``, only rows whose JSON
        metadata satisfy all provided constraints are considered.
        """
        ...

    async def delete(self, ids: list[str]) -> None:
        """Delete documents by ID."""
        ...

    async def delete_by_source_key(self, source_key: str) -> None:
        """Delete all documents with the given source_key (for idempotency)."""
        ...

    async def ensure_collection(self) -> None:
        """Create table/collection if it does not exist."""
        ...

    async def ensure_index(self) -> None:
        """Create HNSW index if it does not exist."""
        ...
