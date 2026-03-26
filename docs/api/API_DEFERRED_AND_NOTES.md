# API: Deferred Items and Open Questions

This document tracks fields, endpoints, and behaviors that are **explicitly deferred** or **TBD** so the team stays aligned. Update this file when decisions are made or when items are scheduled for a future release.

---

## Resolved (v0.2.0)

### Lesson outline: `sections` (content scope)

- **Status:** Resolved in v0.2.0.
- **Resolution:** `section` and `subSection` added as optional string fields to `LessonOutlineRequest`. Values come from the content catalog / ingestion pipeline.
- **Previous concern:** Unclear what values to use and how to handle chapters without clear sections. Decision: accept as optional, best-effort scoping.

### Endpoint routing: `workflow` field vs endpoint path

- **Status:** Resolved in v0.2.0.
- **Resolution:** Endpoint path is the workflow discriminator (e.g. `/generate/lesson-outline`). No `workflow` field in request body. Team B's Template Pack included `workflow` as a required body field; Team A decided against it to avoid redundancy and mismatch bugs.

---

## Deferred / Develop Later

### Workflow 2: Assessment Generation Tool — API contract TBD

- **Status:** Deferred. Workflow 2 scope changed from narrow MCQ transform to full Assessment Generation Tool (per Prof. Shafae, 2026-02-24).
- **Current state:** `POST /generate/assessment-transform` endpoint and its schemas (`AssessmentTransformRequest`, `AssessmentTransformResponse`) are retained as placeholders in the spec. They will be replaced once the new Workflow 2 contract is designed.
- **Next step:** Await Template Pack from Project B for Workflow 2, or draft a proposal from Team A and validate with Prof. Shafae. Then replace placeholder endpoint/schemas.

### Assessment transform: batch (multiple questions)

- **Status:** Deferred, but now expected to be core to the new Workflow 2 scope (batch generation is the default behavior in the Assessment Generation Tool).
- **Next step:** Will be addressed as part of the Workflow 2 contract redesign.

### Assessment transform: structured rubric

- **Status:** Deferred, but now explicitly required by the new Workflow 2 scope (criteria + performance levels).
- **Next step:** Will be addressed as part of the Workflow 2 contract redesign.

### `POST /retrieve` endpoint

- **Status:** Deferred. Removed from spec in v0.2.0.
- **Reason:** Retrieval happens internally in the RAG pipeline during generation. No current use case for a standalone public retrieval endpoint.
- **Next step:** Re-evaluate if Team B needs direct OER search without generation.

### `POST /telemetry/log` endpoint

- **Status:** Deferred. Removed from spec in v0.2.0.
- **Reason:** Engine logs telemetry internally. No current use case for a client-facing telemetry ingestion endpoint.
- **Next step:** Re-evaluate if client-side metrics collection is needed.

### Content catalog endpoint (`GET /content/structure`)

- **Status:** Discussed but not yet added to spec.
- **Reason:** The Engine should expose available book/chapter/section structure so Team B can populate dropdowns with valid values. For POC, this could be a static/hardcoded response.
- **Next step:** Define schema and add endpoint when ingestion pipeline structure is finalized.

---

## Clarifications (for team alignment)

### Lesson outline: HTTP handler vs in-process RAG engine

- **Engine:** `LessonOutlinePipeline` + `Retriever` + `Generator` + pluggable prompts under `app/core/rag/`. Retrieval uses pgvector with optional metadata filters aligned to `LessonOutlineRequest` (chapter, section, subSection, book). Chunks are passed through **in retrieval order** (no merge/dedup). LLM output is parsed into `LessonOutlineGeneratedBody`; **`citations`** are always attached from chunk metadata (one row per chunk; optional `citations` in model JSON is ignored).
- **Prompt templates:** `LessonOutlineRequest.template` (kebab-case) selects the lesson-outline system prompt; values match ``GET /templates/lesson-outline``. `get_lesson_outline_strategy_by_template_id` maps to markdown under `app/core/rag/prompts/templates/`. **`contentType`** selects format rules from `app/core/rag/prompts/rules/` (`format_lecture_notes.md` vs `format_ppt.md`).
- **HTTP:** `POST /generate/lesson-outline` in `app/api/generate.py` calls the pipeline using **`get_retriever`** / **`get_llm`** from `app/deps.py`. Requires `DATABASE_URL`, embedding configuration, indexed OER content, and LLM credentials (e.g. `ANTHROPIC_API_KEY`) for real runs. **502** when the model returns invalid JSON. **`POST /generate/assessment-transform`** remains a **mock** placeholder until Workflow 2 is specified.

### Templates: what they are and who provides them

- **What:** "Templates" are the Engine's 2-3 approved, guardrailed recipe types (per Project A SOW), e.g. "Title/Chapter Q&A", "Role/Scenario Coach", "Instructor task assistant" (lesson outline, assessment transform, etc.).
- **Who provides:** The **Engine (Project A)** defines and serves the list. The Dashboard (Project B) calls `GET /templates/{workflow}` (e.g. `lesson-outline`, `assessment-transform`) and sends the chosen template ``id`` on `POST /generate/lesson-outline` as `template` (Workflow 2 may add an equivalent field later).
- **Routing:** Each workflow keeps its own generate endpoint; template variant is selected by the `template` field on lesson-outline requests (v0.3.0).

### Quality checklists (Workflow 1 and Workflow 2)

- **Decision (2026-02-25):** Checklists are evaluator-side documents derived from the Template Pack. Used during development sampling, sprint demos, and instructor pilot. Not exposed through the Engine API.
- **Engine responsibility:** The Engine should produce structured output elements that the checklists reference (e.g. objective-to-content mappings, checks for understanding tied to objectives, activity time estimates, citations). The checklists evaluate whether these elements are present and adequate.

---

## Changelog

- **2026-03-26 (later):** Documented **wired** `POST /generate/lesson-outline`, `app/deps.py`, format `rules/`, citation order + **`snippet`**, grounding tags in **`slideOutline`**, API **v0.4.0** / `CHANGELOG_API.md`.
- **2026-03-26:** Documented lesson-outline prompt registry (`get_lesson_outline_strategy`, `templates/*.md`, `TemplatedLessonOutlineStrategy`).
- **2026-03-17:** Clarified lesson-outline HTTP vs in-process RAG engine (`app/core/rag/`); citations and metadata filtering behavior documented for Team B alignment.
- **2026-02-25:** Resolved `sections` deferred item (added `section`/`subSection` to request). Resolved `workflow` field routing decision. Deferred `POST /retrieve`, `POST /telemetry/log`, content catalog endpoint. Updated assessment deferred items to reflect Workflow 2 scope change. Added quality checklist clarification.
- **2026-02-18:** Initial deferred list: sections, batch assessment, structured rubric; templates clarification.
