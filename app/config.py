"""Application settings loaded from environment variables and .env file."""

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All config from env vars. pydantic-settings reads env first, falls back to defaults."""

    model_config = {"env_file": ".env", "extra": "ignore"}

    # App
    app_env: str = "development"
    # Per-request wall-clock limit for the full handler (RAG + LLM). 0 = disabled.
    request_timeout_seconds: float = 120.0

    # Provider selection
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-6"
    embedding_provider: str = "voyage"
    embedding_model: str = "voyage-4-lite"
    vector_db_provider: str = "pgvector"
    storage_provider: str = "local"

    # Credentials (empty = validated at provider init time)
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    voyage_api_key: str = ""

    # Storage config
    storage_local_path: str = "data/raw"
    s3_bucket: str = ""
    s3_region: str = "us-east-1"

    # Vector DB config (pgvector)
    database_url: str = ""

    # Ingestion config
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_batch_size: int = 64
    embedding_batch_delay_seconds: float = 0  # set ~21 for Voyage free tier (3 RPM)
    embedding_dimensions: int = 1024  # voyage-4-lite default

    # Dev embedding defaults (used when EMBEDDING_PROVIDER=dev)
    dev_embedding_dimensions: int = 128
    dev_embedding_batch_size: int = 512
    dev_max_chunks: int = 0  # 0 = no cap

    @model_validator(mode="after")
    def _apply_dev_embedding_defaults(self) -> "Settings":
        """Apply fast defaults when EMBEDDING_PROVIDER=dev."""
        if self.embedding_provider.lower() == "dev":
            self.embedding_dimensions = self.dev_embedding_dimensions
            # Make dev runs fast by embedding in large batches.
            if self.embedding_batch_size < self.dev_embedding_batch_size:
                self.embedding_batch_size = self.dev_embedding_batch_size
            # No need to delay for synthetic local embeddings.
            self.embedding_batch_delay_seconds = 0

        if self.vector_db_provider.lower() == "pgvector" and not self.database_url:
            raise ValueError(
                "DATABASE_URL must be set when VECTOR_DB_PROVIDER=pgvector "
                "(set it in your environment or .env; see .env.example)."
            )
        return self
