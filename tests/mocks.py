"""Shared test fakes for ingestion and RAG tests."""

import json

from app.db.vector.filters import VectorMetadataFilter


_FAKE_LESSON_OUTLINE_JSON = json.dumps(
    {
        "outline": "I. Intro\nII. Main ideas\nIII. Wrap-up",
        "keyConcepts": ["Concept A", "Concept B"],
        "misconceptions": ["Common mistake"],
        "checksForUnderstanding": ["Question 1?"],
        "activityIdeas": ["Pair discussion"],
        "slideOutline": None,
    }
)


class FakeLLMProvider:
    """Returns a fixed JSON lesson outline. Records complete() calls."""

    def __init__(self, response_text: str | None = None) -> None:
        self.response_text = response_text or _FAKE_LESSON_OUTLINE_JSON
        self.calls: list[list[dict[str, str]]] = []

    async def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        return self.response_text


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
        *,
        metadata_filter: VectorMetadataFilter | None = None,
    ) -> list[dict]:
        # Cosine similarity with zero vectors: all distances are 0
        results = []
        for i, (doc_id, doc, meta) in enumerate(
            zip(self.ids, self.documents, self.metadatas)
        ):
            if len(results) >= n_results:
                break
            if metadata_filter is not None and metadata_filter.has_any():
                if not _in_memory_metadata_matches(meta, metadata_filter):
                    continue
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


def _in_memory_metadata_matches(meta: dict, f: VectorMetadataFilter) -> bool:
    if f.chapter is not None and str(f.chapter).strip():
        if str(meta.get("chapter") or "") != f.chapter:
            return False
    if f.section is not None and str(f.section).strip():
        if str(meta.get("section") or "") != f.section:
            return False
    if f.sub_section is not None and str(f.sub_section).strip():
        sec = str(meta.get("section") or "")
        if not sec.startswith(f.sub_section):
            return False
    if f.book is not None and str(f.book).strip():
        title = str(meta.get("title") or "").lower()
        if f.book.lower() not in title:
            return False
    return True
