"""Vector store interface. Implementations: chroma, pgvector."""

from typing import Protocol


class VectorStore(Protocol):
    """Protocol for vector storage. Connection-agnostic for ChromaDB and pgvector."""

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
