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
| [CHANGELOG.md](CHANGELOG.md) | Project changelog (app, infra, docs — not API contract). |
| `docs/specs/` | SOW and charter PDFs (Project A, Project B, rolling plan). |

## Repo structure

```
.github/                 # Issue and PR templates
docs/
  api/                   # API contract and API-related notes
  adr/                   # Architecture decision records (ADRs.md, by sprint)
  specs/                 # Project specs (SOW, charter)
CONTRIBUTING.md          # How to contribute (issues, PRs, changelog, ADRs)
CHANGELOG.md             # General project changelog
```

Application code (ingestion, RAG, server) will be added as the team implements per the Sprint 1–4 plan.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for issue/PR flow, changelog rules, and ADRs. In short: use the [issue templates](.github/ISSUE_TEMPLATE/), fill the [PR template](.github/PULL_REQUEST_TEMPLATE.md), and update the relevant changelog.

## License

See [LICENSE](LICENSE).
