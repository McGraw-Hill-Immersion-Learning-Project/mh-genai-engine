"""Tests for POST /ingest/upload."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app.deps import get_ingestion_service, get_storage
from app.main import app


class _FakeStorage:
    """In-memory storage used in tests."""

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    async def get(self, key: str) -> bytes:
        if key not in self._store:
            raise FileNotFoundError(key)
        return self._store[key]

    async def put(self, key: str, data: bytes) -> None:
        self._store[key] = data

    async def list_files(self, prefix: str = "") -> list[str]:
        return [k for k in self._store if k.startswith(prefix)]

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


class _FakeIngestionService:
    """Ingestion service that records ingest() calls without doing real work."""

    def __init__(self, chunks: int = 5) -> None:
        self.ingested: list[str] = []
        self._chunks = chunks

    async def ingest(self, key: str) -> int:
        self.ingested.append(key)
        return self._chunks


@pytest.fixture
def ingest_client():
    """TestClient with storage and ingestion service overridden (no live I/O)."""
    fake_storage = _FakeStorage()
    fake_service = _FakeIngestionService(chunks=7)

    app.dependency_overrides[get_storage] = lambda: fake_storage
    app.dependency_overrides[get_ingestion_service] = lambda: fake_service

    with TestClient(app) as client:
        yield client, fake_storage, fake_service

    app.dependency_overrides.pop(get_storage, None)
    app.dependency_overrides.pop(get_ingestion_service, None)


def _pdf_upload(filename: str = "book.pdf", content: bytes = b"%PDF-1.4 test") -> dict:
    return {"file": (filename, io.BytesIO(content), "application/pdf")}


class TestUploadDocument:
    def test_returns_200_for_pdf(self, ingest_client) -> None:
        client, _, _ = ingest_client
        resp = client.post("/ingest/upload", files=_pdf_upload())
        assert resp.status_code == 200

    def test_response_contains_key_and_chunks(self, ingest_client) -> None:
        client, _, _ = ingest_client
        data = client.post("/ingest/upload", files=_pdf_upload("econ.pdf")).json()
        assert data["key"] == "econ.pdf"
        assert data["chunksStored"] == 7  # camelCase alias (to_camel generator)

    def test_custom_key_is_used(self, ingest_client) -> None:
        client, storage, service = ingest_client
        resp = client.post(
            "/ingest/upload",
            files=_pdf_upload("original.pdf"),
            data={"key": "custom_key.pdf"},
        )
        assert resp.status_code == 200
        assert resp.json()["key"] == "custom_key.pdf"
        assert "custom_key.pdf" in storage._store
        assert service.ingested == ["custom_key.pdf"]

    def test_file_is_persisted_to_storage(self, ingest_client) -> None:
        client, storage, _ = ingest_client
        content = b"%PDF-1.4 hello"
        client.post("/ingest/upload", files=_pdf_upload("save_me.pdf", content))
        assert storage._store.get("save_me.pdf") == content

    def test_ingestion_is_triggered(self, ingest_client) -> None:
        client, _, service = ingest_client
        client.post("/ingest/upload", files=_pdf_upload("trigger.pdf"))
        assert "trigger.pdf" in service.ingested

    def test_unsupported_extension_returns_400(self, ingest_client) -> None:
        client, _, _ = ingest_client
        resp = client.post(
            "/ingest/upload",
            files={"file": ("doc.docx", io.BytesIO(b"data"), "application/octet-stream")},
        )
        assert resp.status_code == 400
        assert "Unsupported" in resp.json()["detail"]

    def test_empty_file_returns_400(self, ingest_client) -> None:
        client, _, _ = ingest_client
        resp = client.post(
            "/ingest/upload",
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_txt_extension_accepted(self, ingest_client) -> None:
        client, _, _ = ingest_client
        resp = client.post(
            "/ingest/upload",
            files={"file": ("notes.txt", io.BytesIO(b"hello world"), "text/plain")},
        )
        assert resp.status_code == 200
        assert resp.json()["key"] == "notes.txt"

    def test_unsafe_chars_in_filename_are_sanitized(self, ingest_client) -> None:
        client, storage, service = ingest_client
        resp = client.post(
            "/ingest/upload",
            files={"file": ("my book (2024).pdf", io.BytesIO(b"%PDF"), "application/pdf")},
        )
        assert resp.status_code == 200
        returned_key = resp.json()["key"]
        assert " " not in returned_key
        assert "(" not in returned_key
        assert returned_key in storage._store

    def test_idempotent_reupload(self, ingest_client) -> None:
        client, storage, service = ingest_client
        for _ in range(2):
            client.post("/ingest/upload", files=_pdf_upload("repeat.pdf"))
        assert storage._store["repeat.pdf"] == b"%PDF-1.4 test"
        assert service.ingested.count("repeat.pdf") == 2
