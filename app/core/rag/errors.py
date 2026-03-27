"""RAG pipeline errors mapped to HTTP responses."""


class StaleChunkIdsError(ValueError):
    """Regenerate was called with chunk ids not all present in the vector store."""
