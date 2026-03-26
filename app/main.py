"""FastAPI application entry point."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health
from app.api import generate
from app.api import templates
from app.deps import get_settings
from app.providers import get_vector_store
from app.utils import get_logger

logger = get_logger(__name__)


def _configure_logging() -> None:
    """Attach a stderr handler for all ``app.*`` loggers (uvicorn often leaves app loggers quiet).

    ``LOG_LEVEL`` env (default ``INFO``): use ``DEBUG`` for verbose traces (e.g. full RAG prompts).
    """
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    app_log = logging.getLogger("app")
    app_log.setLevel(level)
    if not app_log.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter("%(levelname)s [%(name)s] %(message)s")
        )
        app_log.addHandler(handler)
    app_log.propagate = False


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


_configure_logging()

app = create_app()
