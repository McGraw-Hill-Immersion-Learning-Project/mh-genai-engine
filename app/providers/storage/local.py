"""Local filesystem storage (reads from data/). Stub — implement when needed."""

import asyncio
from pathlib import Path

from app.config import settings


class LocalStorageProvider:
    """StorageProvider implementation backed by local filesystem."""

    def __init__(self, base_path: str | None = None) -> None:
        self._base = Path(base_path or settings.storage_local_path)

    def _resolve(self, key: str) -> Path:
        return self._base / key

    async def get(self, key: str) -> bytes:
        path = self._resolve(key)
        return await asyncio.to_thread(path.read_bytes)

    async def put(self, key: str, data: bytes) -> None:
        path = self._resolve(key)

        def _write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        await asyncio.to_thread(_write)

    async def list_files(self, prefix: str = "") -> list[str]:
        def _list() -> list[str]:
            if not self._base.exists():
                return []
            all_files = [
                str(p.relative_to(self._base))
                for p in self._base.rglob("*")
                if p.is_file()
            ]
            if prefix:
                all_files = [f for f in all_files if f.startswith(prefix)]
            return sorted(all_files)

        return await asyncio.to_thread(_list)

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        await asyncio.to_thread(path.unlink, True)