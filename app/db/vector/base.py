"""Vector store interface. Implementation: pgvector."""

from typing import Protocol


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

    async def query(
        self,
        embedding: list[float],
        n_results: int = 10,
    ) -> list[dict]:
        """Query by embedding vector. Return list of matches with metadata."""
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
