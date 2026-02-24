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
- Provider abstractions: LLM (Gemini, Anthropic), embeddings, storage (local/S3).
- Vector DB layer: `app/db/vector/` with ChromaDB and pgvector stubs.
- Data folder: `data/raw/`, `data/processed/`, `data/samples/`.
- Unit test structure mirroring `app/`; health check test.
- `.env.example` with provider/model selection vars; `app/config.py` (pydantic-settings).
- Runbook updated with local run steps.

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2026-02-18

### Added

- Changelog and project doc structure.
