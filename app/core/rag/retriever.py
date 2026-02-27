"""Query vector store and assemble context window for the generator."""

from app.db.vector.base import VectorStore
from app.providers.embeddings.base import EmbeddingProvider


class Retriever:
    """Embed a query and fetch the top-k most relevant chunks from the vector store."""

    def __init__(self, embedder: EmbeddingProvider, vector_store: VectorStore, top_k: int = 5):
        self._embedder = embedder
        self._vector_store = vector_store
        self._top_k = top_k

    async def retrieve(self, query: str) -> list[dict]:
        """Return top-k chunks relevant to the query."""
        embeddings = await self._embedder.embed([query], input_type="query")
        results = await self._vector_store.query(embeddings[0], n_results=self._top_k)
        return results
