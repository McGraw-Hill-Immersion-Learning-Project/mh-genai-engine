# Contributing

## Issues and PRs

- **Issues:** Prefer a [template](.github/ISSUE_TEMPLATE/) (Bug, Feature, Task) or open a blank issue. Add labels as needed.
- **PRs:** Fill the [PR template](.github/PULL_REQUEST_TEMPLATE.md). For docs/config-only changes, you can use the [lighter template](.github/PULL_REQUEST_TEMPLATE/docs_only.md) (add `?expand=1&template=docs_only.md` to the new PR URL).

## Changelog

- **API contract changes** (endpoints, request/response): update [docs/api/CHANGELOG_API.md](docs/api/CHANGELOG_API.md) under `[Unreleased]`.
- **Other changes** (app, infra, docs): update [CHANGELOG.md](CHANGELOG.md) under `[Unreleased]`.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Omit empty sections.

## Code and review

- Follow project style and run any existing checks.
- PRs should be reviewed before merge; keep scope focused.

## Architecture and decisions

Significant architecture decisions are recorded in **[docs/adr/ADRs.md](docs/adr/ADRs.md)** (one file, grouped by sprint). Add new ADRs under the relevant sprint section; format: Decision, Rationale, Alternatives, Cost, Consequences, Status.
