# Changelog

All notable changes to this project (app, ingestion, guardrails, infra, docs) will be documented in this file.

**API contract changes** are in [docs/api/CHANGELOG_API.md](docs/api/CHANGELOG_API.md).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

(Omit any section that has no entries.)

## [Unreleased]

### Added

- **`app/deps.py`:** FastAPI dependencies for `get_settings`, `get_retriever`, `get_llm` (used by generate routes).
- **Startup (pgvector):** `app/main.py` lifespan calls `ensure_collection` / `ensure_index` when `VECTOR_DB_PROVIDER=pgvector` so the first request or ingest is less likely to hit missing-relation errors.
- **`LOG_LEVEL`:** optional env (see `.env.example`); `DEBUG` enables verbose `app.*` logs (e.g. full RAG prompt traces).
- **`pytest.ini`:** filter for `UnsupportedFieldAttributeWarning` (Pydantic 2.12 + FastAPI body validation noise with `alias_generator`).
- **`LessonOutlineRequest.template`:** optional kebab-case prompt variant id (default `default`); validated against the lesson-outline template catalog in `app/core/rag/prompts/registry.py`. Use `get_lesson_outline_strategy_by_template_id` to select the system prompt.
- **RAG (lesson outline):** `Retriever` (embed query + vector search), `Generator` (strict JSON → `LessonOutlineGeneratedBody`, citations from chunk metadata), `LessonOutlinePipeline` (embedding query vs metadata filters). Pluggable `LessonOutlinePromptStrategy`, `get_lesson_outline_strategy()`, and markdown templates under `app/core/rag/prompts/templates/` with `{retrieved_context}` and optional `<grounded ref="N">` guidance.
- **Vector metadata filters:** `VectorMetadataFilter` and `VectorStore.query(..., metadata_filter=...)` implemented for pgvector (SQL) and in-memory test store. Pipeline maps `LessonOutlineRequest` chapter/section/subSection/book into filters; semantic embed text uses learning objective + audience + session length.
- **`LessonOutlineGeneratedBody`** Pydantic model (LLM body without citations); `LessonOutlineResponse` subclasses it and adds citations.
- **Anthropic LLM:** `AnthropicLLMProvider` using `anthropic` Python SDK (`>= 0.80`, `AsyncAnthropic.messages.create`). Dependency added in `requirements.txt`.
- **LLM contract docs:** `LLMProvider` and prompt strategies document provider-agnostic `role`/`content` chat turns; Anthropic adapter maps to Messages API.
- Tests: `tests/core/rag/`, extended `tests/db/vector/test_pgvector.py` (metadata filter), `tests/providers/test_llm_anthropic.py`.

### Changed

- **`POST /generate/lesson-outline`:** wired to **`LessonOutlinePipeline`** + real **`Retriever`** / **`Generator`** (no fixed mock body). **`POST /generate/assessment-transform`** remains mock/placeholder.
- **Citations:** one row per retrieved chunk, stable order for **`<grounded ref="i">`**; **`Citation.snippet`** is a normalized, 50-character preview (full cleanup belongs in ingestion, e.g. Docling later).
- **Prompts:** `contentType` selects **`format_lecture_notes.md`** vs **`format_ppt.md`** rules; templates instruct **`<grounded>`** in both `outline` and **`slideOutline`** (no `[Ref i]`).
- **`app/main.py`:** `warnings.filterwarnings` for `UnsupportedFieldAttributeWarning`; configures `app` logger from **`LOG_LEVEL`**.
- **Templates HTTP API (breaking):** `GET /templates` removed in favor of `GET /templates/{workflow}` with `workflow` ∈ `lesson-outline` | `assessment-transform`. Lesson-outline template ids exposed to clients: `default`, `lecture-scaffold-one-shot`.
- **`app/core/rag/__init__.py`:** no longer re-exports pipeline types at package import (avoids import cycles with `app.models.generate`); import from submodules (e.g. `app.core.rag.generator`).
- **RAG lesson-outline prompts:** `template_strategy.py` implements `TemplatedLessonOutlineStrategy` (markdown templates + `str.format()` for request fields and `{retrieved_context}`). Templates live under `app/core/rag/prompts/templates/`. `get_lesson_outline_strategy(style_id)` registry: `default` → `default_lesson_outline.md`, `lecture_scaffold_one_shot` → `lecture_scaffold_one_shot.md` (research-backed variant; see `templates/System Prompt 1.md`).

### Added

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
- TOC now uses a hybrid strategy: embedded PDF bookmarks are preferred when present (author-intended structure); Docling's visual `SECTION_HEADER` detection is used as a fallback for PDFs that lack bookmarks (common in OER).
- PDF metadata title is read via `pypdfium2` (Docling transitive dep) since Docling does not surface embedded metadata directly.
- `docling>=2.81.0` added to `requirements.txt`.
- Chunker TOC resolution tests decoupled from the parser — they now construct `ParsedDocument` directly, making chunker logic independent of Docling's visual heading inference.
- Docs: `README`, `docs/runbook.md`, `docs/local-dev.md`, `docs/adr/README.md`, `docs/api/API_DEFERRED_AND_NOTES.md`, `docs/api/CHANGELOG_API.md`, `docs/ingestion-plan.md` updated for RAG, metadata filters, Anthropic SDK, and HTTP mock vs engine behavior.
- Docs: `README`, `docs/runbook.md`, `docs/local-dev.md`, `docs/adr/README.md`, `docs/api/API_DEFERRED_AND_NOTES.md`, `docs/api/CHANGELOG_API.md`, `docs/api/openapi.yaml`, `docs/ingestion-plan.md` updated for RAG, metadata filters, Anthropic SDK, wired lesson-outline, citations, and grounding.

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2026-02-18

### Added

- Changelog and project doc structure.
