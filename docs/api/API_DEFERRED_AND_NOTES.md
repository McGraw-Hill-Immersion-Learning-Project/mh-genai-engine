# API: Deferred Items and Open Questions

This document tracks fields, endpoints, and behaviors that are **explicitly deferred** or **TBD** so the team stays aligned. Update this file when decisions are made or when items are scheduled for a future release.

---

## Deferred / Develop Later

### Lesson outline: `sections` (content scope)

- **Status:** Deferred. Not added to `LessonOutlineRequest` in v0.
- **Reason:** Unclear what values to use and how to handle chapters that don’t have clear section separation (e.g. flat structure, single long chapter).
- **Next step:** Product/Engine team to define: (1) section identifier format (e.g. section titles, IDs from ingestion), (2) behavior when chapter has no sections (ignore field vs. treat whole chapter as one section). Then add optional `sections` (e.g. `string[]`) to the request.

### Assessment transform: batch (multiple questions)

- **Status:** Deferred. Current contract supports a single question per request.
- **Location:** `POST /generate/assessment-transform` — request has single `question` + `options`.
- **Next step:** If batch is needed, introduce e.g. `questions: array` and a corresponding batch response shape; document in changelog as a non-breaking addition or new endpoint.

### Assessment transform: structured rubric

- **Status:** Deferred. Response uses a single `rubric` string (e.g. markdown).
- **Reason:** Structured rubric (criteria + performance levels) can be added once format is agreed (e.g. `rubricCriteria: array of { criterion, levels }`).
- **Next step:** Define structured `RubricCriterion` (or similar) schema and add optional `rubricCriteria` to `AssessmentTransformResponse` in a future version.

---

## Clarifications (for team alignment)

### Templates: what they are and who provides them

- **What:** “Templates” are the Engine’s 2–3 approved, guardrailed recipe types (per Project A SOW), e.g. “Title/Chapter Q&A”, “Role/Scenario Coach”, “Instructor task assistant” (lesson outline, assessment transform, etc.).
- **Who provides:** The **Engine (Project A)** defines and serves the list. The Dashboard (Project B) calls `GET /templates` to list available templates and then sends the chosen template id (or equivalent) when calling generate/transform endpoints.
- **Open question:** Whether generation requests include a `templateId` explicitly or the endpoint implies the template (e.g. lesson-outline vs assessment-transform). Current design uses one endpoint per workflow; if we add multiple templates per workflow later, we may need `templateId` in the request.

---

## Changelog

- **2026-02-18:** Initial deferred list: sections, batch assessment, structured rubric; templates clarification.
