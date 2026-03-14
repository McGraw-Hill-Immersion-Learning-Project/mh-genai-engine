"""Shared test fakes for ingestion and RAG tests."""


class FakeEmbeddingProvider:
    """Returns fixed-dimension zero vectors. No API calls."""

    def __init__(self, dimensions: int = 8) -> None:
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return zero vectors of configured dimension for each text."""
        return [[0.0] * self.dimensions for _ in texts]


class InMemoryVectorStore:
    """In-memory vector store for tests. Implements VectorStore protocol."""

    def __init__(self) -> None:
        self.ids: list[str] = []
        self.documents: list[str] = []
        self.embeddings: list[list[float]] = []
        self.metadatas: list[dict] = []

    async def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] | None = None,
    ) -> list[str]:
        if metadatas is None:
            metadatas = [{}] * len(documents)
        ids: list[str] = []
        for i, (doc, emb, meta) in enumerate(
            zip(documents, embeddings, metadatas)
        ):
            source_key = meta.get("source_key", "")
            chunk_id = meta.get("chunk_id", i)
            doc_id = f"{source_key}_{chunk_id}"
            ids.append(doc_id)
            self.ids.append(doc_id)
            self.documents.append(doc)
            self.embeddings.append(emb)
            self.metadatas.append(meta)
        return ids

    async def query(
        self,
        embedding: list[float],
        n_results: int = 10,
    ) -> list[dict]:
        # Cosine similarity with zero vectors: all distances are 0
        results = []
        for i, (doc_id, doc, meta) in enumerate(
            zip(self.ids, self.documents, self.metadatas)
        ):
            if len(results) >= n_results:
                break
            results.append(
                {
                    "id": doc_id,
                    "content": doc,
                    "metadata": meta,
                    "distance": 0.0,
                }
            )
        return results

    async def delete(self, ids: list[str]) -> None:
        to_remove = set(ids)
        new_ids, new_docs, new_embs, new_metas = [], [], [], []
        for i, doc_id in enumerate(self.ids):
            if doc_id not in to_remove:
                new_ids.append(self.ids[i])
                new_docs.append(self.documents[i])
                new_embs.append(self.embeddings[i])
                new_metas.append(self.metadatas[i])
        self.ids, self.documents, self.embeddings, self.metadatas = (
            new_ids,
            new_docs,
            new_embs,
            new_metas,
        )

    async def delete_by_source_key(self, source_key: str) -> None:
        to_remove = [
            i for i, m in enumerate(self.metadatas)
            if m.get("source_key") == source_key
        ]
        for i in reversed(to_remove):
            del self.ids[i]
            del self.documents[i]
            del self.embeddings[i]
            del self.metadatas[i]

    async def ensure_collection(self) -> None:
        pass

    async def ensure_index(self) -> None:
        pass
