"""Application settings loaded from environment variables and .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All config from env vars. pydantic-settings reads env first, falls back to defaults."""

    model_config = {"env_file": ".env", "extra": "ignore"}

    # App
    app_env: str = "development"

    # Provider selection
    llm_provider: str = "gemini"
    llm_model: str = "gemini-3-flash-preview"
    embedding_provider: str = "gemini"
    embedding_model: str = "text-embedding-004"
    vector_db_provider: str = "chroma"
    storage_provider: str = "local"

    # Credentials (empty = validated at provider init time)
    gemini_api_key: str = ""
    anthropic_api_key: str = ""

    # Storage config
    storage_local_path: str = "data/raw"
    s3_bucket: str = ""
    s3_region: str = "us-east-1"

    # Vector DB config
    chroma_host: str | None = None
    chroma_port: int = 8000
    database_url: str = ""
