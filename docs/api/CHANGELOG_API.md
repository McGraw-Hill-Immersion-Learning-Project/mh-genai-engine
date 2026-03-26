# Engine API Changelog

All notable changes to the **Engine API contract** (endpoints, request/response shapes, versions) are documented here.

**Other project changes** (app, infra, docs): see [CHANGELOG.md](../../CHANGELOG.md) in the repo root.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the API version follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html). For **breaking changes**, add a migration note under the version.

(Omit any section that has no entries.)

## [Unreleased]

### Notes (implementation only; contract unchanged)

- OpenAPI paths and JSON shapes for `POST /generate/lesson-outline` are **unchanged**. The Engine now has an in-process **RAG implementation** (`LessonOutlinePipeline`, etc.) and internal schema split (`LessonOutlineGeneratedBody` for LLM JSON vs `LessonOutlineResponse` with citations). The **HTTP route still returns mock data** until the handler is wired to the pipeline.
- Citations in live RAG responses will be built from **vector chunk metadata** (`title`, `page_number`, `chapter`, `section`), not from optional `citations` in model JSON (ignored if present).
- **Prompt styles (internal):** `get_lesson_outline_strategy(style_id)` selects markdown templates (`default`, `lecture_scaffold_one_shot`). No request field exposes this yet; wire `Generator` when connecting the HTTP handler.

## [0.2.0] - 2026-02-25

### Added

- `LessonOutlineRequest`: new fields `book`, `section`, `subSection`, `learningObjective` (singular string), `contentType` (enum: lecture_notes, ppt), `count` (integer), `audienceLevel` (enum: beginner, intermediate, advanced), `regeneratedResponse` (boolean, logging-only).
- New `LogEntry` schema for internal workflow audit logging (not exposed as endpoint).

### Changed

- `Citation` schema: now uses `title`, `page` (optional), `chapter`, `section`. Replaces previous `chapter`, `section`, `sourceId`, `excerpt`.
- `POST /generate/assessment-transform`: added description noting Workflow 2 scope is being redesigned; endpoint and schemas retained as placeholders.
- `TelemetryEvent` schema: added description clarifying it is used internally (no public endpoint currently).

### Removed

- `LessonOutlineRequest`: removed `learningObjectives` (array), `audience`, `tone`, `timeAllowed`, `externalResources`.
- `POST /retrieve` endpoint and associated schemas (`RetrieveRequest`, `RetrieveResponse`, `RetrievedChunk`) — deferred, no current use case; retrieval happens internally in the RAG pipeline.
- `POST /telemetry/log` endpoint — deferred, no current use case; Engine logs telemetry internally.

### Migration notes

- **Breaking:** `LessonOutlineRequest` fields changed. Callers must update to use `learningObjective` (singular), `contentType`, `count`, `audienceLevel` instead of the removed fields.
- **Breaking:** `Citation` schema fields changed. Callers must update to use `title`, `page`, `chapter`, `section` instead of `sourceId`, `excerpt`.

## [0.1.0] - 2026-02-18

### Added

- Initial API contract (OpenAPI 3.1): `POST /generate/lesson-outline`, `POST /generate/assessment-transform`, `POST /retrieve`, `GET /templates`, `POST /telemetry/log`.
- Request/response schemas with citations, templates, and error responses.
