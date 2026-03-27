"""Ingest endpoint: upload a document and trigger the ingestion pipeline."""

import re
from pathlib import PurePosixPath
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.deps import get_ingestion_service, get_storage
from app.models.ingest import UploadResponse
from app.providers.storage.base import StorageProvider

router = APIRouter(tags=["ingest"])

_ALLOWED_EXTENSIONS = {".pdf", ".txt"}
_UNSAFE_CHARS = re.compile(r"[^\w.\-]")


def _derive_key(filename: str) -> str:
    """Sanitize an uploaded filename into a safe storage key."""
    name = PurePosixPath(filename).name or "upload"
    return _UNSAFE_CHARS.sub("_", name)


@router.post("/ingest/upload", response_model=UploadResponse, response_model_by_alias=True)
async def upload_document(
    file: UploadFile = File(description="Document file (PDF or plain text) to ingest"),
    key: Optional[str] = Form(default=None, description="Optional storage key override"),
    storage: StorageProvider = Depends(get_storage),
    service=Depends(get_ingestion_service),
) -> UploadResponse:
    """Upload a document, store it, and run the ingestion pipeline.

    The file is saved to the configured storage backend (local or S3) and then
    parsed, chunked, embedded, and written to the vector store.  Re-uploading
    the same key replaces existing vectors (idempotent).
    """
    suffix = PurePosixPath(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type {suffix!r}. Allowed: {sorted(_ALLOWED_EXTENSIONS)}",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if key:
        storage_key = _UNSAFE_CHARS.sub("_", key)
    else:
        storage_key = _derive_key(file.filename or "upload")

    try:
        await storage.put(storage_key, data)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to store document: {e}",
        ) from e

    try:
        chunks_stored = await service.ingest(storage_key)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ingestion failed: {e}",
        ) from e

    return UploadResponse(key=storage_key, chunks_stored=chunks_stored)
