"""Orchestrate RAG: retrieve context, generate response via LLM."""

from __future__ import annotations

from app.db.vector.filters import VectorMetadataFilter
from app.models.generate import (
    LessonOutlineRegenerateRequest,
    LessonOutlineRequest,
    LessonOutlineResponse,
)

from app.core.rag.errors import StaleChunkIdsError
from app.core.rag.generator import Generator
from app.core.rag.prompts.base import LessonOutlineRefinementPromptStrategy
from app.core.rag.retriever import Retriever
from app.utils import get_logger

logger = get_logger(__name__)


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
        logger.info("lesson_outline_retrieval n_chunks=%d", len(chunks))
        return await self._generator.generate(chunks, request)

    async def run_regenerate(
        self,
        request: LessonOutlineRegenerateRequest,
        refinement_strategy: LessonOutlineRefinementPromptStrategy,
    ) -> LessonOutlineResponse:
        """Load chunks by id when ``chunk_ids`` is set; else embed instructions + outline slice."""
        ids = request.chunk_ids or []
        if ids:
            chunks = await self._retriever.retrieve_by_ids(ids)
            if len(chunks) != len(ids):
                raise StaleChunkIdsError(
                    "Unknown or stale chunkIds: not all requested ids were found in the vector store"
                )
        else:
            parts: list[str] = []
            ri = (request.refinement_instructions or "").strip()
            if ri:
                parts.append(ri)
            outline = (request.previous_outline.outline or "").strip()
            if outline:
                parts.append(outline[:2000])
            query = " ".join(parts).strip() or "lesson outline refinement"
            chunks = await self._retriever.retrieve(
                query,
                n_results=self._n_results,
                metadata_filter=None,
            )
        logger.info("lesson_outline_refinement_retrieval n_chunks=%d", len(chunks))
        return await self._generator.regenerate(chunks, request, refinement_strategy)
