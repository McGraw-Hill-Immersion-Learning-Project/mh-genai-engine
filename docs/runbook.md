# Runbook

How to run and deploy the Engine, and how secrets are managed. Per ADR-006: secrets live in env (local: `.env` in repo root; demo: platform env). **Never commit `.env` or real keys.** This doc must be complete before 3/23.

---

## Required env vars

None required for health check. See `.env.example` in repo root for all available vars. Credentials required only when using the corresponding provider (e.g. `ANTHROPIC_API_KEY` when `LLM_PROVIDER=anthropic`).

| Variable | Purpose | Example / notes |
|----------|---------|-----------------|
| APP_ENV | Environment name | `development`, `staging`, `production` |
| LLM_PROVIDER | LLM backend | `anthropic` (default), `gemini` |
| LLM_MODEL | Model name | `claude-sonnet-4-6`, `gemini-3-flash-preview` |
| EMBEDDING_PROVIDER | Embedding backend | `voyage` (default), `gemini` |
| EMBEDDING_MODEL | Embedding model name | `voyage-4-lite`, `voyage-3-large`, `text-embedding-004` |
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
4. **No Docker:** `pip install -r requirements.txt` then `uvicorn app.main:app --reload`
5. Verify: `curl http://localhost:8000/health` returns `{"status":"ok"}`

### Testing (full coverage including DB)

To run **all** tests, including the pgvector adapter tests (4 tests that hit Postgres), do the following in order:

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
   Pytest loads `.env` automatically (see `tests/conftest.py`), so the pgvector tests will run and you should see **68 tests** (64 passed + 4 pgvector). If the db is not running or `DATABASE_URL` is missing, the 4 pgvector tests are **skipped** and you’ll see 64 passed, 4 skipped.

To run only the pgvector tests: `pytest -m pgvector -v`.

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

*Last updated: 2026-03-04. Keep this doc in sync with the backend and deploy process.*
