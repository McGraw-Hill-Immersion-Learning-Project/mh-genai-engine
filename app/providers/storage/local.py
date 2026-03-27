"""Local filesystem storage (reads from data/)."""

import asyncio
from pathlib import Path


class LocalStorageProvider:
    """Read documents from local filesystem."""

    def __init__(self, base_path: str = "data/raw") -> None:
        self._base_path = Path(base_path)

    async def get(self, key: str) -> bytes:
        """Read a file by key and return its bytes."""
        path = self._base_path / key
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {key}")
        return await asyncio.to_thread(path.read_bytes)

    async def list_files(self, prefix: str = "") -> list[str]:
        """List file keys with optional prefix filter."""
        if not self._base_path.exists():
            return []

        def _list() -> list[str]:
            keys: list[str] = []
            for p in self._base_path.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(self._base_path)
                    key = str(rel).replace("\\", "/")
                    if key.startswith(prefix):
                        keys.append(key)
            return sorted(keys)

        return await asyncio.to_thread(_list)

    async def put(self, key: str, data: bytes) -> None:
        """Write bytes to a file by key, creating parent directories as needed."""
        path = self._base_path / key
        await asyncio.to_thread(self._write, path, data)

    @staticmethod
    def _write(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    async def delete(self, key: str) -> None:
        """Delete a file by key."""
        raise NotImplementedError("LocalStorageProvider.delete() not implemented")
