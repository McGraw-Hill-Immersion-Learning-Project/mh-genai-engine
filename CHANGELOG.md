# Changelog

All notable changes to this project (app, ingestion, guardrails, infra, docs) will be documented in this file.

**API contract changes** are in [docs/api/CHANGELOG_API.md](docs/api/CHANGELOG_API.md).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

(Omit any section that has no entries.)

## [Unreleased]

### Added

- **RAG (lesson outline):** `Retriever` (embed query + vector search), `Generator` (strict JSON → `LessonOutlineGeneratedBody`, citations from chunk metadata), `LessonOutlinePipeline` (embedding query vs metadata filters). Pluggable `LessonOutlinePromptStrategy` and registry; default template `app/core/rag/prompts/default_lesson_outline.md` with `{retrieved_context}` and optional `<grounded ref="N">` guidance.
- **Vector metadata filters:** `VectorMetadataFilter` and `VectorStore.query(..., metadata_filter=...)` implemented for pgvector (SQL) and in-memory test store. Pipeline maps `LessonOutlineRequest` chapter/section/subSection/book into filters; semantic embed text uses learning objective + audience + session length.
- **`LessonOutlineGeneratedBody`** Pydantic model (LLM body without citations); `LessonOutlineResponse` subclasses it and adds citations.
- **Anthropic LLM:** `AnthropicLLMProvider` using `anthropic` Python SDK (`>= 0.80`, `AsyncAnthropic.messages.create`). Dependency added in `requirements.txt`.
- **LLM contract docs:** `LLMProvider` and prompt strategies document provider-agnostic `role`/`content` chat turns; Anthropic adapter maps to Messages API.
- Tests: `tests/core/rag/`, extended `tests/db/vector/test_pgvector.py` (metadata filter), `tests/providers/test_llm_anthropic.py`.

- FastAPI project skeleton with health check endpoint (`GET /health`).
- Dockerfile and docker-compose.yml for local dev (ADR-004, ADR-005).
- RAG / ingestion layout: `app/core/rag/`, `app/core/ingestion/`.
- Provider abstractions: LLM (Anthropic, Gemini), embeddings (Voyage, Gemini), storage (local/S3).
- Provider factory functions (`get_llm_provider`, `get_embedding_provider`) with env-based selection and API-key validation.
- `pytest-asyncio` dependency for async provider tests.
- Vector DB layer: `app/db/vector/` — pgvector implementation; `chroma.py` placeholder.
- Data folder: `data/raw/`, `data/processed/`, `data/samples/`.
- Unit test structure mirroring `app/`; health check test.
- `.env.example` with provider/model selection vars (defaults: Anthropic + Voyage); `app/config.py` (pydantic-settings).
- Runbook updated with local run steps.
- `DocumentParser`: extracts per-page text, title, and TOC from PDFs via PyMuPDF; plain-text fallback for non-PDF files.
- `TextChunker`: splits pages using `RecursiveCharacterTextSplitter`; resolves `chapter` and `section` from TOC by page number; every chunk carries `source_key`, `title`, `page_number`, `chapter`, `section`, `chunk_id`.
- `chunk_size` and `chunk_overlap` added to `Settings` (configurable via `.env`).
- `PyMuPDF` and `langchain-text-splitters` in `requirements.txt`.
- Parser/chunker tests with synthetic PDF fixtures via PyMuPDF conftest.

### Changed

- `DocumentParser` now uses Docling (standard pipeline) instead of PyMuPDF for PDF parsing. Docling performs layout analysis to produce structured Markdown (headings, tables, lists) per page rather than raw flat text, improving chunk quality for RAG retrieval.
- TOC is now inferred from visual `SECTION_HEADER` items (levels 1–2) detected by Docling rather than embedded PDF bookmarks, which are frequently absent in OER PDFs.
- PDF metadata title is read via `pypdfium2` (Docling transitive dep) since Docling does not surface embedded metadata directly.
- `docling>=2.81.0` added to `requirements.txt`.
- Chunker TOC resolution tests decoupled from the parser — they now construct `ParsedDocument` directly, making chunker logic independent of Docling's visual heading inference.
- Docs: `README`, `docs/runbook.md`, `docs/local-dev.md`, `docs/adr/README.md`, `docs/api/API_DEFERRED_AND_NOTES.md`, `docs/api/CHANGELOG_API.md`, `docs/ingestion-plan.md` updated for RAG, metadata filters, Anthropic SDK, and HTTP mock vs engine behavior.

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2026-02-18

### Added

- Changelog and project doc structure.
