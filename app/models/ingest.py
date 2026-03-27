"""Pydantic schemas for ingest endpoints."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class UploadResponse(BaseModel):
    """Response returned after a successful document upload and ingestion."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    key: str
    chunks_stored: int
