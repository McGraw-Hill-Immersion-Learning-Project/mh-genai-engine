# Runbook

How to run and deploy the Engine, and how secrets are managed. Per ADR-006: secrets live in env (local: `.env` in repo root; demo: platform env). **Never commit `.env` or real keys.** This doc must be complete before 3/23.

---

## Required env vars

None required for health check. See `.env.example` in repo root for all available vars. Credentials required only when using the corresponding provider (e.g. `ANTHROPIC_API_KEY` when `LLM_PROVIDER=anthropic`).

| Variable | Purpose | Example / notes |
|----------|---------|-----------------|
| APP_ENV | Environment name | `development`, `staging`, `production` |
| REQUEST_TIMEOUT_SECONDS | Per-request wall-clock limit for HTTP handlers (RAG + LLM) | Default `120`; `0` disables. Exceeded → **504** `{"detail":"Request timed out"}`. See `app/middleware/timeout.py`. |
| LOG_LEVEL | Verbosity for `app.*` loggers | Default `INFO`; set `DEBUG` for full RAG prompt traces in logs |
| LLM_PROVIDER | LLM backend | `anthropic` (default), `gemini` |
| LLM_MODEL | Model name | `claude-sonnet-4-6`, `gemini-3-flash-preview` |
| EMBEDDING_PROVIDER | Embedding backend | `voyage` (default), `gemini`, `dev` (synthetic local) |
| EMBEDDING_MODEL | Embedding model name | `voyage-4-lite`, `voyage-3-large`, `text-embedding-004`, `local-dev` |
| EMBEDDING_DIMENSIONS | Vector size for pgvector | `1024` (voyage-4-lite). When `EMBEDDING_PROVIDER=dev`, this is overridden by `DEV_EMBEDDING_DIMENSIONS` for speed. |
| DEV_EMBEDDING_DIMENSIONS | Dev embedding dimension | Default `128` (used only when `EMBEDDING_PROVIDER=dev`) |
| DEV_EMBEDDING_BATCH_SIZE | Dev embedding batch size | Default `512` (used only when `EMBEDDING_PROVIDER=dev`) |
| DEV_MAX_CHUNKS | Optional dev chunk cap | `0` = no cap; set e.g. `200` for very fast runs |
| DATABASE_URL | Postgres + pgvector connection | Required for ingestion; default: `postgresql://mhgenai:mhgenai@localhost:5432/mhgenai` |
| ANTHROPIC_API_KEY | Anthropic API key | Required when `LLM_PROVIDER=anthropic` |
| VOYAGE_API_KEY | Voyage AI API key | Required when `EMBEDDING_PROVIDER=voyage` |
| GEMINI_API_KEY | Gemini API key | Required when using Gemini for LLM or embeddings |

---

## Where secrets live

- **Local:** `.env` in repo root (gitignored). Create from `.env.example` if present; never commit `.env`.
- **Demo (App Runner):** Same variable names, set in AWS App Runner → Service → Environment. No file upload; configure in console or IaC.

---

## Local run

1. `cp .env.example .env` — copy template and set any values (optional for health check only)
2. **Vector DB (pgvector):** For ingestion, start Postgres with pgvector: `docker compose up db -d`. This runs Postgres on port 5432. Set `DATABASE_URL=postgresql://mhgenai:mhgenai@localhost:5432/mhgenai` in `.env` (or use the default).
3. **Docker (full stack):** `docker compose up --build` — builds and runs the app + db on ports 8000 and 5432
4. **No Docker:** `pip install -r requirements.txt` then `uvicorn app.main:app --reload` (or `fastapi dev` from the repo root)
5. Verify: `curl http://localhost:8000/health` returns `{"status":"ok"}`

### RAG pipeline (lesson outline)

The **engine** implements lesson-outline RAG in-process (see `app/core/rag/`). **`POST /generate/lesson-outline`** (`app/api/generate.py`) is wired to this stack via **`app/deps.py`** (`get_retriever`, `get_llm`).

| Piece | Role |
|-------|------|
| `Retriever` | Embeds a semantic query string, runs pgvector similarity search with optional `VectorMetadataFilter` (chapter, section, sub-section prefix, **`book`** = case-insensitive substring on **`metadata.title` or `metadata.source_key`**). Returns chunks **in retrieval order** (no merge/dedup). |
| `Generator` | Builds chat turns via a `LessonOutlinePromptStrategy`, calls `LLMProvider.complete`, parses JSON into `LessonOutlineGeneratedBody`, attaches **`citations`** (one per chunk, same order as `### Passage [i]`; each includes stable **`chunkId`** for vector row id). Strips any `citations` key from raw LLM JSON. |
| `LessonOutlinePipeline` | `build_embedding_query()` = learning objective + audience + session length; `metadata_filter_for_request()` = structural fields from `LessonOutlineRequest`. **`run_regenerate`:** optional **`chunkIds`** → fetch by id; else embed refinement text + outline slice with **no** metadata filters. |
| `app/core/rag/prompts/` | `TemplatedLessonOutlineStrategy` loads markdown from `prompts/templates/` and injects **format rules** from `prompts/rules/` (`format_lecture_notes.md` vs `format_ppt.md`) based on `contentType`. Templates include `{retrieved_context}` and **`<grounded ref="N">`** guidance for `outline` and **`slideOutline`**. Registry: `get_lesson_outline_strategy_by_template_id` maps kebab-case API `template` ids to internal keys (`default`, `lecture_scaffold_one_shot`). |

**Startup:** When `VECTOR_DB_PROVIDER=pgvector`, `app/main.py` lifespan attempts **`ensure_collection`** / **`ensure_index`** so the chunks table exists before traffic or ingest.

**Regenerate:** `POST /generate/lesson-outline/regenerate` — body is **`previousOutline`**, **`refinementInstructions`**, optional **`chunkIds`** (from prior **`citations[].chunkId`**). Stale or unknown ids when **`chunkIds`** is non-empty → **422**. Invalid LLM JSON → **502**.

**Failure modes:** Invalid LLM JSON → **502** from generate/regenerate. Request wall-clock over **`REQUEST_TIMEOUT_SECONDS`** → **504** (all routes). Empty retrieval still runs the LLM (prompt explains no passages).

**Tests:** `pytest tests/core/rag/` (mocked store + LLM). Full suite also covers API + integration paths (`pytest tests/` — on the order of **120+** tests with DB up).

**LLM:** With `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` set, `get_llm_provider()` returns `AnthropicLLMProvider` (`anthropic` SDK ≥ 0.80, `AsyncAnthropic.messages.create`).

### Testing (full coverage including DB)

To run **all** tests, including the **pgvector** integration tests (Postgres + SQL metadata filters), do the following in order:

1. **Start the database:** From the repo root, run:
   ```bash
   docker compose up db -d
   ```
   Wait until Postgres is ready (a few seconds). Optionally check with `docker compose ps` (db should be “Up (healthy)”).

2. **Ensure `.env` has `DATABASE_URL`:** If you don’t have a `.env` file, run `cp .env.example .env`. The default `DATABASE_URL=postgresql://mhgenai:mhgenai@localhost:5432/mhgenai` works when the db container is running on port 5432.

3. **Run the full test suite:** From the repo root:
   ```bash
   pytest
   ```
   Pytest loads `.env` automatically (see `tests/conftest.py`). If the DB is up and `DATABASE_URL` is set, **pgvector-marked** tests run; if not, they are **skipped**. Run `pytest` (or `pytest -q`) and check the summary for passed vs skipped. Typical full run is on the order of **120+** collected tests.

To run only the pgvector tests: `pytest -m pgvector -v`.

RAG unit/integration tests (mocked vector store + LLM): `pytest tests/core/rag/ -v`.

### Ingesting a sample book chapter

To run the full pipeline (read → parse → chunk → embed → store) on a PDF:

1. **Start the database** (if not already running): `docker compose up db -d`
2. **Put a PDF in `data/raw/`** — e.g. download a chapter or use the Economics OER from the [ingestion plan](ingestion-plan.md). Example: `data/raw/Economics_Ch1.pdf`
3. **Set env** — In `.env` you need at least:
   - `DATABASE_URL=postgresql://mhgenai:mhgenai@localhost:5432/mhgenai`
   - `VOYAGE_API_KEY=<your-key>` (used for embeddings)
   - **Voyage free tier (3 RPM):** set `EMBEDDING_BATCH_SIZE=3` and `EMBEDDING_BATCH_DELAY_SECONDS=21` to avoid rate-limit errors.
4. **Run the ingest CLI** from the repo root:
   ```bash
   python scripts/ingest.py run Economics_Ch1.pdf
   ```
   List available files: `python scripts/ingest.py list`. Help: `python scripts/ingest.py --help`.

Re-running the same file is idempotent (existing chunks for that file are replaced). Each embedding configuration (provider/model/dimensions) writes to its own pgvector `chunks_*` table, so changing embedding configs does not mix data across different indexes.

### Local dev embeddings (synthetic) — run ingest without Voyage

To run ingestion **without any Voyage API key or external service**, use the synthetic dev embedding provider. It’s deterministic and optimized for speed; it is intended for local development and plumbing tests (not for evaluating retrieval quality).

1. **Install dependencies** — from the repo root:
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the database** (if not already running): `docker compose up db -d`
3. **Configure `.env`** — Set:
   - `EMBEDDING_PROVIDER=dev`
   - `EMBEDDING_MODEL=local-dev`
   - `DATABASE_URL=postgresql://mhgenai:mhgenai@localhost:5432/mhgenai`

Optional speed knobs (dev only):
- `DEV_EMBEDDING_DIMENSIONS=128`
- `DEV_EMBEDDING_BATCH_SIZE=512`
- `DEV_MAX_CHUNKS=200`

4. **Run the ingest CLI**:
   ```bash
   python scripts/ingest.py run eepsam.pdf
   ```

---

## Demo / App Runner deploy

*(Steps to deploy the Engine to App Runner for demo. Fill in when we have a container image and service.)*

1. TBD (build image, push to ECR or other registry)
2. TBD (create or update App Runner service, set env vars)
3. TBD (how to verify: hit service URL, smoke test)

---

## Rotation (changing secrets)

1. Generate or obtain new key/secret.
2. **Local:** Update `.env` in repo root, restart the app.
3. **Demo:** Update env vars in App Runner service config, redeploy or restart the service.
4. Revoke or expire the old key if applicable.
5. *(Optional)* Document rotation date in this section or in a changelog.

---

## Who can change secrets

- **Local:** Each developer manages their own `.env` in repo root (personal/dev keys only; no shared demo keys in personal env).
- **Demo:** TBD (e.g. Tech Lead and sponsor only; document who has access to App Runner env config).

---

*Last updated: 2026-03-26. Keep this doc in sync with the backend and deploy process.*
