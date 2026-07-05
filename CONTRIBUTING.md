# Contributing to OpsPulse

Thank you for helping build Issue-to-Deploy scaffolding for JDK 8 microservices.

## Before you start

1. Read [doc/用户接入指南.md](doc/用户接入指南.md) for the three-layer delivery model.
2. Run `scripts/check-prerequisites.sh` to verify your environment.
3. Copy `.env.example` to `.env` (never commit `.env`).

## Issue workflow

- Use `.github/ISSUE_TEMPLATE/auto-dev-feature.yml` or `auto-dev-bugfix.yml`.
- Include YAML frontmatter per `schemas/issue-spec.v1.json`.
- Bugfix issues **must** include reproduction steps (`## 复现步骤` or `## Reproduction Steps`).
- Validate locally:

```bash
python scripts/validate-issue-spec.py examples/issues/001-order-service-feature.md
```

## Pull request process

1. Fork and create a feature branch from `main`.
2. Keep changes focused; avoid unrelated refactors.
3. Ensure `validate-schema` CI passes.
4. Fill out the PR template checklist.
5. Link the related Issue.

## Code conventions

- **Docs in Chinese** live under `doc/` (planning, guides).
- **Code and config** use English (README, scripts, YAML, JSON Schema).
- No `sample-backend/` in this repository (see D11 in `doc/DECISIONS.md`).
- Minimal, focused diffs — match existing style.

## Development layout

| Path | Purpose |
|------|---------|
| `schemas/` | Issue Spec JSON Schema |
| `scripts/` | Validation and prerequisite checks |
| `examples/issues/` | Reference Issue markdown files |
| `harness-templates/` | Pipeline stage placeholders |
| `local-runner/` | Local CI skeleton |
| `mcp-server/` | Phase 2 — FastMCP tools |

## Questions

Open a GitHub Issue with the `question` label or refer to `doc/实施计划.md`.
