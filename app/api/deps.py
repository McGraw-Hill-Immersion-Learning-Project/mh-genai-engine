"""FastAPI Depends() helpers for provider injection."""

from fastapi import Request

from app.core.ingestion.service import IngestionService
from app.db.vector.pgvector import PGVectorStore
from app.providers.embeddings.bge import BGEEmbeddingProvider
from app.providers.storage.local import LocalStorageProvider


def get_vector_store(request: Request) -> PGVectorStore:
    return request.app.state.vector_store


def get_embedder(request: Request) -> BGEEmbeddingProvider:
    return request.app.state.embedder


def get_storage(request: Request) -> LocalStorageProvider:
    return request.app.state.storage


def get_ingestion(request: Request) -> IngestionService:
    return request.app.state.ingestion
