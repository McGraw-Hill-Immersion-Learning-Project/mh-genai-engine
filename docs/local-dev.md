# Local development: API and ingestion

This is a focused guide for running the Engine locally, including the ingestion CLI with the fast dev embedding provider.

---

## 1. Prerequisites

- Python 3.12 (with `venv`)
- Docker (for Postgres + pgvector)

From the repo root:

```bash
python -m venv venv
venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
```

---

## 2. Environment and database

1. Copy the example env and tweak as needed:

```bash
cp .env.example .env
```

2. Start Postgres with pgvector:

```bash
docker compose up db -d
```

3. Ensure your `.env` has at least:

```env
DATABASE_URL=postgresql://mhgenai:mhgenai@localhost:5432/mhgenai
```

Chunk tables and HNSW indexes are created automatically on app startup or via the ingestion pipeline. Tables are created per embedding config to avoid dimension/model conflicts (e.g. `chunks_dev_128_<hash>` vs `chunks_voyage_1024_<hash>`).

---

## 3. Running the API locally

With the virtualenv active and `.env` in place:

```bash
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

You should see:

```json
{"status":"ok"}
```

---

## 4. Ingesting a PDF with dev embeddings (no API keys)

For local plumbing tests and quick feedback, use the synthetic dev embedding provider. It is deterministic and fast, but not semantically meaningful.

1. Put a PDF under `data/raw/`, for example:

```text
data/raw/eepsam.pdf
```

2. In `.env`, set:

```env
EMBEDDING_PROVIDER=dev
EMBEDDING_MODEL=local-dev

# Fast dev defaults (override if you like)
DEV_EMBEDDING_DIMENSIONS=64     # e.g. 64 or 128
DEV_EMBEDDING_BATCH_SIZE=512
DEV_MAX_CHUNKS=200              # 0 = no cap; 200 is good for quick runs
```

3. Run the ingest CLI from the repo root:

```bash
python scripts/ingest.py run eepsam.pdf
```

You should see step‑by‑step progress logs and a final line like:

```text
Done. Stored 114 chunks.
```

All chunks and embeddings are written to a provider/model/dimension specific `chunks_*` table in Postgres.

---

## 5. Ingesting with Voyage (production‑like)

When you want realistic embeddings, switch to the Voyage provider:

1. In `.env`:

```env
EMBEDDING_PROVIDER=voyage
EMBEDDING_MODEL=voyage-4-lite
EMBEDDING_DIMENSIONS=1024
VOYAGE_API_KEY=sk-...

# For Voyage free tier (3 RPM)
EMBEDDING_BATCH_SIZE=3
EMBEDDING_BATCH_DELAY_SECONDS=21
```

2. Run the same ingest command:

```bash
python scripts/ingest.py run eepsam.pdf
```

This path is slower and uses your Voyage quota, but produces real semantic embeddings.

---

## 6. Verifying what’s in the database

To inspect stored chunks and embeddings, connect to the db container:

```bash
docker compose exec db psql -U mhgenai -d mhgenai
```

Example checks:

```sql
-- list the chunk tables created for different embedding configs
\dt chunks*

-- pick a table name from the list above, then run checks like:
SELECT COUNT(*) FROM chunks_dev_128_XXXXXXXX;

SELECT COUNT(*)
FROM chunks_dev_128_XXXXXXXX
WHERE metadata->>'source_key' = 'eepsam.pdf';

SELECT id, left(content, 120) AS preview, metadata
FROM chunks_dev_128_XXXXXXXX
WHERE metadata->>'source_key' = 'eepsam.pdf'
LIMIT 5;
```

