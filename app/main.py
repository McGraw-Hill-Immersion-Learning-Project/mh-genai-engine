"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI

from app.api import health
from app.config import Settings
from app.core.ingestion.service import IngestionService
from app.db.vector.pgvector import PGVectorStore
from app.providers.embeddings.bge import BGEEmbeddingProvider
from app.providers.storage.local import LocalStorageProvider


@lru_cache
def get_settings() -> Settings:
    """Load settings from env and .env."""
    return Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise providers on startup, clean up on shutdown."""
    vector_store = PGVectorStore()
    await vector_store.initialize()

    embedder = BGEEmbeddingProvider()       # downloads model on first run
    storage = LocalStorageProvider()
    ingestion = IngestionService(storage, embedder, vector_store)

    app.state.vector_store = vector_store
    app.state.embedder = embedder
    app.state.storage = storage
    app.state.ingestion = ingestion

    yield

    await vector_store._pool.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""
    app = FastAPI(
        title="MH GenAI Engine",
        description="RAG-powered backend",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    return app


app = create_app()
