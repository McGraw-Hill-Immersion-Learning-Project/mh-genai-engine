"""Orchestrate RAG: retrieve context, generate response via LLM."""

from app.core.rag.generator import Generator
from app.core.rag.retriever import Retriever


class RAGPipeline:
    """End-to-end RAG: query → retrieve → generate."""

    def __init__(self, retriever: Retriever, generator: Generator):
        self._retriever = retriever
        self._generator = generator

    async def query(self, question: str) -> dict:
        """Run the full RAG pipeline. Returns answer and source chunks."""
        chunks = await self._retriever.retrieve(question)
        answer = await self._generator.generate(question, chunks)
        return {
            "answer": answer,
            "sources": [
                {"source": c["metadata"].get("source"), "score": c["score"]}
                for c in chunks
            ],
        }
