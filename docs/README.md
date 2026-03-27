# Docs

- **api/** — Engine API contract (OpenAPI), API changelog, deferred/notes.
- **adr/** — Architecture Decision Records ([ADRs.md](adr/ADRs.md)); [README](adr/README.md) maps ADRs to implementation.
- **runbook.md** — How to run/deploy the Engine and manage secrets (ADR-006). Includes **RAG pipeline** (wired `POST /generate/lesson-outline`, `deps.py`, `templates/` + `rules/`, citations + grounding). Local run: `docker compose up`, `uvicorn app.main:app --reload`, or `fastapi dev`.
- **local-dev.md** — API + ingestion; **§7** summarizes RAG and the live lesson-outline endpoint.
- **ingestion-plan.md** — Chunk metadata and how it feeds retrieval filters/citations.
- **specs/** — Project A/B SOW and charter PDFs (reference).

For contribution flow and changelogs, see the [repo README](../README.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).
