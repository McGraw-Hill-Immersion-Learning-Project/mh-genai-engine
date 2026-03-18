"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI

from app.api import health
from app.api import generate
from app.api import templates
from app.config import Settings
from app.providers import get_vector_store
from utils import get_logger

logger = get_logger(__name__)

@lru_cache
def get_settings() -> Settings:
    """Load settings from env and .env."""
    return Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup/shutdown."""
    settings = get_settings()

    # Ensure pgvector collection and index exist on startup so that the first
    # ingestion run (or tests) do not fail with missing relation errors.
    try:
        if settings.vector_db_provider.lower() == "pgvector":
            vector_store = get_vector_store(settings)
            await vector_store.ensure_collection()
            await vector_store.ensure_index()
    except Exception as e:
        # On startup we don't want to crash the entire app if the DB is
        # temporarily unavailable; ingestion will surface errors explicitly.
        logger.warning("DB init failed: %s", e)

    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""
    app = FastAPI(
        title="MH GenAI Engine",
        description="RAG-powered backend",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(templates.router)
    app.include_router(generate.router)
    return app


app = create_app()
