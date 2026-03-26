# Architecture Decision Records (ADRs)

All architecture decisions in one place, grouped by sprint.

- [Sprint 1](#sprint-1)

**Format per ADR:** Decision, Rationale, Alternatives considered, Cost, Consequences/Positives, Status.

---

## Sprint 1

**Deciders:** Bao, Pragnya, Harsh, John  
**Review:** Rishabh, Anirudha  
**Status:** Proposed → set to Accepted after team/sponsor sign-off. Charter DoD: decision pack in repo.

---

### ADR-001: LLM Provider Strategy

- **Decision:** We will pay for OpenAI API for the demo (by 3/23). For local dev, use Gemini free tier or any other provider of choice.
- **Rationale:** Provider-agnostic design so we can switch later. OpenAI for demo (familiar, stable); free-tier or personal choice for dev keeps cost down while building.
- **Alternatives considered:** Anthropic, local models.
- **Cost estimate:** $100–200 for 6-month POC (demo); dev is free tier / own choice.
- **Consequences/Positives:** Abstraction from day one for easier swap; demo is OpenAI until we decide otherwise.
- **Status:** Approved

---

### ADR-002: Vector Database

- **Decision:** pgvector (PostgreSQL extension) for Sprint 1–2; evaluate hosted vector DBs (Pinecone, Qdrant) later if needed.
- **Rationale:** pgvector runs inside PostgreSQL, which we already use for the app DB, no extra service to run or manage. HNSW indexing gives fast approximate nearest-neighbour search. Keeps the stack simple for POC: one database, one Docker container.
- **Alternatives considered:** ChromaDB (lightweight but a separate service; less mature operationally), Qdrant (purpose-built but adds infra complexity), Pinecone (hosted, no ops, but $70+/mo and vendor lock-in from day one).
- **Cost:** Free (OSS, runs in existing Postgres container). Pinecone ~$70/mo if we migrate for hosted staging/demo.
- **Consequences/Positives:** Single DB for relational + vector data; cosine similarity via HNSW index. Migration path to a dedicated vector DB is straightforward, same embedding interface, swap the store implementation.
- **Status:** Approved

---

### ADR-003: RAG Framework

- **Decision:** Custom RAG pipeline (no framework).
- **Rationale:** LangChain and LlamaIndex add significant abstraction overhead and opinionated data models that conflict with our provider-agnostic design (ADR-001, ADR-007). For a focused POC with a known retrieval pattern (embed → HNSW search → LLM generate), a custom pipeline is simpler, easier to debug, and has no framework lock-in.
- **Alternatives considered:** LangChain (heavy abstractions, fast to prototype but hard to customise), LlamaIndex (good for document pipelines but overkill for POC scope), Haystack (similar trade-offs).
- **Cost:** None (OSS dependencies only).
- **Consequences/Positives:** Full control over retrieval logic (e.g. score threshold filtering at 0.65), prompt construction, and metadata handling. Every step is explicit and testable.
- **Implementation:** `app/core/rag/` (retriever, generator, pipeline, pluggable prompts: `TemplatedLessonOutlineStrategy`, `get_lesson_outline_strategy`, `prompts/templates/*.md`, `prompts/rules/*.md`); `POST /generate/lesson-outline` wired via `app/deps.py`. See `docs/runbook.md` § RAG pipeline.
- **Status:** Approved

---

### ADR-004: Backend Framework

- **Decision:** FastAPI.
- **Rationale:** Team is most familiar with it; Python ecosystem; good OpenAPI support; async. No formal evaluation of other frameworks.
- **Alternatives considered:** None formally; FastAPI chosen for familiarity.
- **Cost:** None (OSS).
- **Consequences/Positives:** Lock into Python; frontend may use a different language → shared types (e.g. OpenAPI) need to be maintained.
- **Status:** Approved

---

### ADR-005: Deployment Strategy (POC)

- **Decision:** Docker Compose for local dev; AWS App Runner for demo. Use EC2 later only if we need SSH, full control, or different cost profile—same Docker image, so transition is straightforward.
- **Rationale:** App Runner = minimal ops, deploy container and get a URL. Docker everywhere so we can move to EC2 (or ECS) without changing the app.
- **Alternatives considered:** EC2, GCP, Digital Ocean. Chose App Runner first for speed; EC2 if we outgrow it.
- **Cost:** TBD until we deploy (App Runner billed per vCPU/memory + requests).
- **Consequences/Positives:** Low ops for POC; single platform (AWS) for now. App is containerized so we can move to another cloud (e.g. GCP Cloud Run, Azure Container Apps) if needed—no app lock-in. Smooth path to EC2 on AWS if we need it.
- **Status:** Proposed

---

### ADR-006: Key Management

- **Decision:** All secrets live in `.env` in repo root (gitignored; never committed). Env vars for config; no personal accounts for shared/demo. (Runbook = doc that describes how to run/deploy and how to set up/rotate secrets. Rotation = update values in `.env`, redeploy/restart; plan TBD.)
- **Rationale:** SOW/Charter: no personal student accounts; project- or sponsor-owned credentials by 3/23. Single file in root keeps it simple and provider-agnostic (repo is the backend).
- **Alternatives considered:** AWS Secrets Manager / SSM vs env-only; chose env-only for POC simplicity and portability.
- **Cost:** N/A (env-only for POC).
- **Consequences/Positives:** Keys never in repo or logs. Runbook (`docs/runbook.md`) must document required vars, where `.env` lives (repo root), and how to rotate; to be written before 3/23.
- **Status:** Proposed
