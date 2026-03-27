"""Stable vector row ids from ingestion metadata (must match store primary keys)."""


def chunk_document_id(metadata: dict, fallback_index: int) -> str:
    """Primary key string: ``{source_key}_{chunk_id}`` (same rule as pgvector add_documents)."""
    m = metadata or {}
    source_key = m.get("source_key", "")
    cid = m.get("chunk_id", fallback_index)
    return f"{source_key}_{cid}"
