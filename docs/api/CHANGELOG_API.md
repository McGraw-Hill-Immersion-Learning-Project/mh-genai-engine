# Engine API Changelog

All notable changes to the **Engine API contract** (endpoints, request/response shapes, versions) are documented here.

**Other project changes** (app, infra, docs): see [CHANGELOG.md](../../CHANGELOG.md) in the repo root.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the API version follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html). For **breaking changes**, add a migration note under the version.

(Omit any section that has no entries.)

## [Unreleased]

### Notes (implementation only; contract unchanged)

- Citations in live RAG responses will be built from **vector chunk metadata** (`title`, `page_number`, `chapter`, `section`), not from optional `citations` in model JSON (ignored if present).

## [0.3.0] - 2026-03-26

### Added

- `LessonOutlineRequest`: optional `template` field (string, default `default`). Values are **kebab-case** ids returned by `GET /templates/lesson-outline`. The Engine maps `template` to the corresponding lesson-outline system prompt (`get_lesson_outline_strategy_by_template_id` in-process).
- `GET /templates/{workflow}` with `workflow` enum `lesson-outline` | `assessment-transform`. Returns `{ "templates": [ { "id", "name", "description" } ] }` for that workflow only.

### Changed (breaking)

- **Removed** `GET /templates`. Callers must use `GET /templates/lesson-outline` and/or `GET /templates/assessment-transform`.

### Migration notes

- Replace `GET /templates` with the appropriate `GET /templates/{workflow}` path. Lesson-outline prompt ids are now **kebab-case** (`default`, `lecture-scaffold-one-shot`), not legacy workflow slugs like `lesson-outline`.
- When calling `POST /generate/lesson-outline`, omit `template` to keep the default prompt, or set `template` to an id from `GET /templates/lesson-outline`.

### Notes

- The Engine has an in-process **RAG implementation** (`LessonOutlinePipeline`, etc.). The **HTTP** `POST /generate/lesson-outline` handler may still return **mock** data until wired to the pipeline; the `template` field is validated on the request regardless.

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
