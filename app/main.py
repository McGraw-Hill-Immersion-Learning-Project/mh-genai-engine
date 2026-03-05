"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from functools import lru_cache

from fastapi import FastAPI

from app.api import health
from app.api import generate
from app.api import templates
from app.config import Settings
from app.schemas.health import HealthResponse

@lru_cache
def get_settings() -> Settings:
    """Load settings from env and .env."""
    return Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup/shutdown. Add provider init here when built."""
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
