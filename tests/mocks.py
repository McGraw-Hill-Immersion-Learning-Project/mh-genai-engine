"""Shared test fakes for ingestion and RAG tests."""

import asyncio
import json

from app.db.vector.filters import VectorMetadataFilter
from app.db.vector.ids import chunk_document_id


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


_REFINED_LESSON_OUTLINE_JSON = json.dumps(
    {
        "outline": "REFINED: I. Intro with warm-up\nII. Main ideas\nIII. Wrap-up",
        "keyConcepts": ["Concept A", "Concept B", "Warm-up"],
        "misconceptions": ["Common mistake"],
        "checksForUnderstanding": ["Question 1?"],
        "activityIdeas": ["Pair discussion", "Think-pair-share"],
        "slideOutline": None,
    }
)


class RefinementDistinctFakeLLMProvider(FakeLLMProvider):
    """Returns generate-shaped JSON for create prompts, distinct JSON when system prompt is refinement."""

    def __init__(self) -> None:
        super().__init__()
        self.response_text = _FAKE_LESSON_OUTLINE_JSON

    async def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        system = (messages[0].get("content") or "") if messages else ""
        low = system.lower()
        if "refining" in low and "existing lesson outline" in low:
            return _REFINED_LESSON_OUTLINE_JSON
        return self.response_text


class AdaptiveLessonOutlineFakeLLM:
    """Fake LLM: adds a non-empty slideOutline when the system prompt is for PPT."""

    def __init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []

    async def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        system = messages[0]["content"] if messages else ""
        data = json.loads(_FAKE_LESSON_OUTLINE_JSON)
        if "- Content type: ppt" in system:
            data["slideOutline"] = (
                "Slide 1: Title — Bone structure\n"
                "Slide 2: Learning objectives\n"
                "Slide 3: Discussion"
            )
        else:
            data["slideOutline"] = None
        return json.dumps(data)


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
            doc_id = chunk_document_id(meta, i)
            ids.append(doc_id)
            self.ids.append(doc_id)
            self.documents.append(doc)
            self.embeddings.append(emb)
            self.metadatas.append(meta)
        return ids

    async def get_by_ids(self, ids: list[str]) -> list[dict]:
        """Rows in *ids* order; first occurrence wins when duplicate ids exist."""
        first_index: dict[str, int] = {}
        for i, doc_id in enumerate(self.ids):
            if doc_id not in first_index:
                first_index[doc_id] = i
        out: list[dict] = []
        for doc_id in ids:
            idx = first_index.get(doc_id)
            if idx is None:
                continue
            out.append(
                {
                    "id": doc_id,
                    "content": self.documents[idx],
                    "metadata": dict(self.metadatas[idx]),
                }
            )
        return out

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


def seed_default_lesson_outline_store() -> InMemoryVectorStore:
    """In-memory chunks aligned with default API tests (chapter 6, anatomy title)."""
    store = InMemoryVectorStore()
    meta = {
        "title": "Anatomy & Physiology",
        "page_number": 142,
        "chapter": "6",
        "section": "6.3",
        "source_key": "ap.pdf",
        "chunk_id": "0",
    }

    async def _seed() -> None:
        await store.add_documents(
            [
                "Compact bone is organized into osteons (Haversian systems). "
                "Spongy bone forms trabeculae; osteoblasts deposit matrix."
            ],
            [[0.0] * 8],
            [meta],
        )

    asyncio.run(_seed())
    return store


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
        needle = f.book.lower()
        title = str(meta.get("title") or "").lower()
        src = str(meta.get("source_key") or "").lower()
        if needle not in title and needle not in src:
            return False
    return True
