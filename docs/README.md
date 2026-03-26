# Docs

- **api/** — Engine API contract (OpenAPI), API changelog, deferred/notes.
- **adr/** — Architecture Decision Records ([ADRs.md](adr/ADRs.md)); [README](adr/README.md) maps ADRs to implementation.
- **runbook.md** — How to run/deploy the Engine and manage secrets (ADR-006). Includes **RAG pipeline** overview, pgvector + metadata filters, and testing. Local run: `docker compose up` or `uvicorn app.main:app --reload`.
- **local-dev.md** — API + ingestion; **§7** summarizes RAG vs mock `generate` endpoint.
- **ingestion-plan.md** — Chunk metadata and how it feeds retrieval filters/citations.
- **specs/** — Project A/B SOW and charter PDFs (reference).

For contribution flow and changelogs, see the [repo README](../README.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).
