# Architecture Decision Records (ADRs)

We use **Architecture Decision Records** to capture architecturally significant decisions and their rationale. This follows the practice popularized by [Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) and summarized at [adr.github.io](https://adr.github.io/).

**[ADRs.md](ADRs.md)** — Single doc for all ADRs, grouped by sprint. One place to find every decision; add new sprints as sections (e.g. `## Sprint 2`). Format per ADR: Decision, Rationale, Alternatives, Cost, Consequences, Status.

| Sprint | ADRs |
|--------|------|
| [Sprint 1](ADRs.md#sprint-1) | 001–006 (Provider, Vector DB, RAG, Backend, Deployment, Key Management) |

---

## Implementation status

Where each ADR is reflected in the codebase:

| ADR | Implementation |
|-----|----------------|
| **ADR-001** (LLM Provider) | `app/providers/llm/` — Protocol in `base.py` (provider-agnostic chat turns: `role` + `content`). **Anthropic:** `anthropic.py` uses `anthropic` SDK ≥ 0.80 (`AsyncAnthropic.messages.create`). **Gemini:** `gemini.py` still a stub. Embeddings: `app/providers/embeddings/` (`voyage`, `gemini`, `dev`). Factory in `app/providers/__init__.py` selects via `LLM_PROVIDER` / `EMBEDDING_PROVIDER`. Defaults: Anthropic + Voyage. |
| **ADR-002** (Vector DB) | `app/db/vector/` — Protocol in `base.py`; **`pgvector.py`** implements storage, query, and optional **`metadata_filter`** (`VectorMetadataFilter` in `filters.py`). `chroma.py` is unused placeholder. Selected via `VECTOR_DB_PROVIDER`. |
| **ADR-003** (RAG Framework) | **Custom pipeline (no LangChain):** `app/core/rag/` — `retriever.py`, `generator.py`, `pipeline.py`, `prompts/` (`template_strategy.py`, `registry.py`, `templates/*.md`, `rules/*.md` for lecture vs ppt format). Ingestion remains `app/core/ingestion/`. |
| **ADR-004** (FastAPI) | `app/main.py`, `app/api/` — FastAPI app with health router. |
| **ADR-005** (Docker Compose) | `Dockerfile`, `docker-compose.yml` — `docker compose up` runs the app locally. |
| **ADR-006** (Key Management) | `app/config.py` (pydantic-settings), `.env.example`, [docs/runbook.md](../runbook.md) — env vars for config and secrets. |
