"""Orchestrate RAG: retrieve context, generate response via LLM."""

from __future__ import annotations

from app.db.vector.filters import VectorMetadataFilter
from app.models.generate import LessonOutlineRequest, LessonOutlineResponse

from app.core.rag.generator import Generator
from app.core.rag.retriever import Retriever


class LessonOutlinePipeline:
    """Embed query, retrieve chunks, generate structured lesson outline."""

    def __init__(
        self,
        retriever: Retriever,
        generator: Generator,
        *,
        n_results: int = 10,
    ) -> None:
        self._retriever = retriever
        self._generator = generator
        self._n_results = n_results

    @staticmethod
    def build_embedding_query(request: LessonOutlineRequest) -> str:
        """Text used for the embedding model (semantic): objective + pedagogy hints."""
        parts = [
            request.learning_objective,
            f"Audience level: {request.audience_level.value}.",
            f"Session length: {request.count} minutes.",
        ]
        return " ".join(p for p in parts if p).strip()

    @staticmethod
    def metadata_filter_for_request(
        request: LessonOutlineRequest,
    ) -> VectorMetadataFilter:
        """Structured filters applied in the vector DB (chapter/section/book, etc.)."""
        return VectorMetadataFilter(
            chapter=request.chapter,
            section=request.section,
            sub_section=request.sub_section,
            book=request.book,
        )

    async def run(self, request: LessonOutlineRequest) -> LessonOutlineResponse:
        query = self.build_embedding_query(request)
        meta_filter = self.metadata_filter_for_request(request)
        chunks = await self._retriever.retrieve(
            query,
            n_results=self._n_results,
            metadata_filter=meta_filter,
        )
        return await self._generator.generate(chunks, request)
