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
| **ADR-001** (LLM Provider) | `app/providers/llm/` — Protocol in `base.py`; skeleton classes: `anthropic.py`, `gemini.py`. `app/providers/embeddings/` — Protocol in `base.py`; skeleton classes: `voyage.py`, `gemini.py`. Factory functions in `app/providers/__init__.py` select provider via `LLM_PROVIDER` / `EMBEDDING_PROVIDER` env vars and validate API keys. Defaults: Anthropic (LLM) + Voyage (embeddings). |
| **ADR-002** (Vector DB) | `app/db/vector/` — Protocol in `base.py`; stubs: `chroma.py`, `pgvector.py`. Selected via `VECTOR_DB_PROVIDER`. |
| **ADR-003** (RAG Framework) | `app/core/rag/`, `app/core/ingestion/` — framework-agnostic; pipeline and service stubs ready for LangChain/custom/LlamaIndex. |
| **ADR-004** (FastAPI) | `app/main.py`, `app/api/` — FastAPI app with health router. |
| **ADR-005** (Docker Compose) | `Dockerfile`, `docker-compose.yml` — `docker compose up` runs the app locally. |
| **ADR-006** (Key Management) | `app/config.py` (pydantic-settings), `.env.example`, [docs/runbook.md](../runbook.md) — env vars for config and secrets. |
