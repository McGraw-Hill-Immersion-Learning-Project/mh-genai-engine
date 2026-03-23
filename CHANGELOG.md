# Changelog

All notable changes to this project (app, ingestion, guardrails, infra, docs) will be documented in this file.

**API contract changes** are in [docs/api/CHANGELOG_API.md](docs/api/CHANGELOG_API.md).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

(Omit any section that has no entries.)

## [Unreleased]

### Added

- FastAPI project skeleton with health check endpoint (`GET /health`).
- Dockerfile and docker-compose.yml for local dev (ADR-004, ADR-005).
- RAG pipeline structure: `app/core/rag/`, `app/core/ingestion/`.
- Provider abstractions: LLM (Anthropic, Gemini), embeddings (Voyage, Gemini), storage (local/S3).
- Provider factory functions (`get_llm_provider`, `get_embedding_provider`) with env-based selection and API-key validation.
- `pytest-asyncio` dependency for async provider tests.
- Vector DB layer: `app/db/vector/` with ChromaDB and pgvector stubs.
- Data folder: `data/raw/`, `data/processed/`, `data/samples/`.
- Unit test structure mirroring `app/`; health check test.
- `.env.example` with provider/model selection vars (defaults: Anthropic + Voyage); `app/config.py` (pydantic-settings).
- Runbook updated with local run steps.
- `DocumentParser`: extracts per-page text, title, and TOC from PDFs via PyMuPDF; plain-text fallback for non-PDF files.
- `TextChunker`: splits pages using `RecursiveCharacterTextSplitter`; resolves `chapter` and `section` from TOC by page number; every chunk carries `source_key`, `title`, `page_number`, `chapter`, `section`, `chunk_id`.
- `chunk_size` and `chunk_overlap` added to `Settings` (configurable via `.env`).
- `PyMuPDF==1.25.3` and `langchain-text-splitters==0.3.8` added to `requirements.txt`.
- 17 unit tests for parser and chunker; synthetic PDF fixtures generated in-process via PyMuPDF conftest.

### Changed

- `DocumentParser` now uses Docling (standard pipeline) instead of PyMuPDF for PDF parsing. Docling performs layout analysis to produce structured Markdown (headings, tables, lists) per page rather than raw flat text, improving chunk quality for RAG retrieval.
- TOC is now inferred from visual `SECTION_HEADER` items (levels 1–2) detected by Docling rather than embedded PDF bookmarks, which are frequently absent in OER PDFs.
- PDF metadata title is read via `pypdfium2` (Docling transitive dep) since Docling does not surface embedded metadata directly.
- `docling>=2.81.0` added to `requirements.txt`.
- Chunker TOC resolution tests decoupled from the parser — they now construct `ParsedDocument` directly, making chunker logic independent of Docling's visual heading inference.

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2026-02-18

### Added

- Changelog and project doc structure.
