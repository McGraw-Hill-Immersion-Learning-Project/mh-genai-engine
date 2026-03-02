"""Orchestrate RAG: retrieve context, generate response via LLM."""

from app.core.rag.generator import Generator
from app.core.rag.retriever import Retriever


class RAGPipeline:
    """End-to-end RAG: query → retrieve → generate."""

    def __init__(self, retriever: Retriever, generator: Generator):
        self._retriever = retriever
        self._generator = generator

    MIN_SCORE = 0.65  # chunks below this are not relevant enough to cite

    async def query(self, question: str) -> dict:
        """Run the full RAG pipeline. Returns answer and source chunks."""
        chunks = await self._retriever.retrieve(question)
        relevant = [c for c in chunks if c["score"] >= self.MIN_SCORE]

        answer = await self._generator.generate(question, relevant)
        return {
            "answer": answer,
            "sources": [
                {
                    "source": c["metadata"].get("source"),
                    "title": c["metadata"].get("title"),
                    "chapter": c["metadata"].get("chapter"),
                    "section": c["metadata"].get("section"),
                    "page_number": c["metadata"].get("page_number"),
                    "score": c["score"],
                }
                for c in relevant
            ],
        }
