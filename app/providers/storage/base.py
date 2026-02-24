"""Document storage interface."""

from typing import Protocol


class StorageProvider(Protocol):
    """Protocol for document storage. Implementations: local, s3."""

    async def get(self, key: str) -> bytes:
        """Read a file by key and return its bytes."""
        ...

    async def put(self, key: str, data: bytes) -> None:
        """Write bytes to a file by key."""
        ...

    async def list_files(self, prefix: str = "") -> list[str]:
        """List file keys with optional prefix filter."""
        ...

    async def delete(self, key: str) -> None:
        """Delete a file by key."""
        ...
