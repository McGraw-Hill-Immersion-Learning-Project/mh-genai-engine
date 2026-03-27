# mh-genai-engine

Content-grounded GenAI **Engine** (Project A) for McGraw Hill’s Instructor Toolkit POC. Provides OER ingestion, RAG with citations, guardrails, template-driven generation, and a stable API consumed by the Instructor Toolkit Dashboard (Project B).

## What this repo is

- **Scope:** Proof-of-concept Engine only (no Dashboard UI; no Connect/SimNet/ALEKS integration).
- **Deliverables (per SOW):** Ingestion pipeline, RAG service with citations, 2–3 approved templates, baseline guardrails, versioned Engine API, validation suite, telemetry.
- **Status:** Early stage — API contract and project docs in place; implementation in progress (execution from week of 2/16 per charter; formal presentations 3/23, 5/4, 6/15, 8/10).

## Key docs

| Doc | Purpose |
|-----|--------|
| [docs/api/openapi.yaml](docs/api/openapi.yaml) | Engine API contract (OpenAPI 3.1) — endpoints, request/response shapes, errors. |
| [docs/api/CHANGELOG_API.md](docs/api/CHANGELOG_API.md) | API version history (Keep a Changelog). |
| [docs/api/API_DEFERRED_AND_NOTES.md](docs/api/API_DEFERRED_AND_NOTES.md) | Deferred API items and open questions (e.g. `sections`, batch assessment, structured rubric). |
| [docs/runbook.md](docs/runbook.md) | How to run, deploy, and manage secrets (ADR-006). |
| [docs/local-dev.md](docs/local-dev.md) | Local dev quickstart: API + ingestion (dev vs Voyage embeddings). |
| [docs/adr/ADRs.md](docs/adr/ADRs.md) | Architecture decisions; [README](docs/adr/README.md) maps ADRs to implementation. |
| [CHANGELOG.md](CHANGELOG.md) | Project changelog (app, infra, docs — not API contract). |
| `docs/specs/` | SOW and charter PDFs (Project A, Project B, rolling plan). |

## Repo structure

```
.github/                 # Issue and PR templates
app/                     # FastAPI backend
  api/                   # HTTP routers (health, generate, templates)
  core/                  # Business logic: rag/ (retriever, generator, pipeline, prompts), ingestion/
  providers/             # LLM, embeddings, storage adapters
  db/                    # Vector store (pgvector; optional metadata filters on query)
  models/                # Pydantic schemas
  deps.py                # FastAPI dependencies (settings, retriever, LLM)
  config.py              # Settings from .env
data/                    # Document storage: raw/, processed/, samples/
docs/
  api/                   # API contract and API-related notes
  adr/                   # Architecture decision records (ADRs.md, implementation map)
  specs/                 # Project specs (SOW, charter)
tests/                   # Unit tests (mirrors app/ structure)
Dockerfile               # Container build
docker-compose.yml       # Local dev: docker compose up
requirements.txt         # Pinned dependencies
.env.example             # Env var template (copy to .env)
CONTRIBUTING.md          # How to contribute (issues, PRs, changelog, ADRs)
CHANGELOG.md             # General project changelog
```

Run locally: `cp .env.example .env` then `docker compose up --build`. Verify: `curl http://localhost:8000/health`.

**Tests (full coverage):** Start the DB with `docker compose up db -d`, ensure `.env` has `DATABASE_URL` (default in `.env.example`), then run `pytest`. See [docs/runbook.md](docs/runbook.md#testing-full-coverage-including-db) for details.

**RAG (lesson outline):** `POST /generate/lesson-outline` runs **`LessonOutlinePipeline`** (`app/api/generate.py` + `app/deps.py`): embed query → **pgvector** retrieval with **metadata filters** (optional **`book`** matches substring on chunk **`title` *or* `source_key`**) → **`Generator`** (pluggable `LessonOutlinePromptStrategy`, templates in `app/core/rag/prompts/templates/`, format rules in `prompts/rules/` by `contentType`). Responses include **`citations`** (one per retrieved chunk; **`chunkId`** + **`snippet`**, etc.) and model text that may use **`<grounded ref="i">`** aligned with `citations[i]`. **`POST /generate/lesson-outline/regenerate`** refines a prior outline; optional **`chunkIds`** replay passages by id. Optional **`REQUEST_TIMEOUT_SECONDS`** (env) caps handler time → **504** if exceeded. Requires `DATABASE_URL`, embedding config, indexed OER, and LLM keys as appropriate. See [runbook — RAG pipeline](docs/runbook.md#rag-pipeline-lesson-outline) and [API changelog](docs/api/CHANGELOG_API.md).

**Ingest a sample chapter:** Put a PDF in `data/raw/`, then `python scripts/ingest.py run <filename>`. Use `python scripts/ingest.py list` to see files. Requires a running DB and either `VOYAGE_API_KEY` (production‑like) or the local dev embedding provider (`EMBEDDING_PROVIDER=dev`, no API key). See [local dev guide](docs/local-dev.md) and [runbook – Ingesting a sample book chapter](docs/runbook.md#ingesting-a-sample-book-chapter).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for issue/PR flow, changelog rules, and ADRs. In short: use the [issue templates](.github/ISSUE_TEMPLATE/), fill the [PR template](.github/PULL_REQUEST_TEMPLATE.md), and update the relevant changelog.

## License

See [LICENSE](LICENSE).
