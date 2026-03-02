"""End-to-end RAG test: ingest Economics_OER.pdf and run a query."""

import asyncio
import json
import os
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from app.core.ingestion.service import IngestionService
from app.core.rag.generator import Generator
from app.core.rag.pipeline import RAGPipeline
from app.core.rag.retriever import Retriever
from app.db.vector.pgvector import PGVectorStore
from app.providers.embeddings.bge import BGEEmbeddingProvider
from app.providers.llm.anthropic import AnthropicLLMProvider
from app.providers.storage.local import LocalStorageProvider


async def main():
    print("Initialising providers...")
    vector_store = PGVectorStore()
    await vector_store.initialize()

    embedder = BGEEmbeddingProvider()
    storage = LocalStorageProvider()
    llm = AnthropicLLMProvider()

    # ── Skip ingestion — already ingested with enriched metadata
    ingestion = IngestionService(storage, embedder, vector_store)
    async with vector_store._pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM document_chunks")
    print(f"\n{count} chunks in DB.")

    # ── Query
    retriever = Retriever(embedder, vector_store, top_k=5)
    generator = Generator(llm)
    pipeline = RAGPipeline(retriever, generator)

    questions = [
        # In-scope
        "What is the difference between microeconomics and macroeconomics?",
        "Explain the law of supply and demand.",
        "What is price elasticity of demand?",
        # Out-of-scope
        "What is the current inflation rate in the United States?",
        "Who will win the next US presidential election?",
        "Write me a Python script to scrape stock prices.",
    ]

    results = []
    for q in questions:
        print(f"\n{'─'*60}")
        print(f"Q: {q}")
        result = await pipeline.query(q)
        print(f"A: {result['answer']}")
        print("Sources:")
        for s in result["sources"]:
            print(f"  - {s['source']} | {s.get('chapter','')} | {s.get('section','')} | p.{s.get('page_number','')} (score: {s['score']:.3f})")
        results.append({"question": q, "answer": result["answer"], "sources": result["sources"]})

    # ── Save results
    os.makedirs("tests/golden/results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"tests/golden/results/{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump({"run_at": timestamp, "results": results}, f, indent=2)
    print(f"\nResults saved to {output_path}")

    await vector_store._pool.close()


if __name__ == "__main__":
    asyncio.run(main())
