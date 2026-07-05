# Changelog

All notable changes to OpsPulse are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0-demo] - 2026-07-05

### Added

- `mcp-server/` FastMCP server with three tools: `parse_issue`, `update_issue_status`, `trigger_pipeline`
- Shared Issue Spec parsers (`opspulse_mcp.parsers`) reused by `scripts/validate-issue-spec.py`
- Local pipeline stages in `local-runner/run-pipeline.sh` (validate → jdk verify → build → image → smoke)
- `scripts/smoke-test.sh` and `scripts/e2e-demo.sh` Gate 2 demo chain
- `docs/quickstart.md` — 30-minute getting started guide
- MCP server unit tests (`mcp-server/tests/`)

### Changed

- `.cursor/mcp.json` — `opspulse` server uses `uv --directory mcp-server run opspulse-mcp`
- `scripts/validate-issue-spec.py` — imports shared validation from `opspulse_mcp`

## [0.0.1-schema] - 2026-07-05

### Added

- Repository skeleton: `.gitignore`, `LICENSE`, `opspulse.yaml`, `.env.example`
- Issue Spec v1 JSON Schema (`schemas/issue-spec.v1.json`)
- Frontmatter validator (`scripts/validate-issue-spec.py`) and unit tests
- Three example Issues (`examples/issues/001–003`)
- GitHub Issue templates (`auto-dev-feature`, `auto-dev-bugfix`)
- Schema validation CI (`.github/workflows/validate-schema.yml`)
- Harness pipeline placeholders (`harness-templates/`)
- Local runner skeleton (`local-runner/run-pipeline.sh`, `docker-compose.yml`)
- JDK8 Dockerfile fixture (`examples/fixtures/deploy/order-service/Dockerfile`)
- Cursor MCP config placeholder (`.cursor/mcp.json`) and agent rules
- Prompts: `issue-to-code.md`, `pipeline-troubleshoot.md`
- Docs: `docs/mcp-setup.md`, `docs/harness-setup.md`
- Prerequisites check script (`scripts/check-prerequisites.sh`)
- `README.md`, `CONTRIBUTING.md`, PR template

### Notes

- No `sample-backend/` per D11
- `opspulse-mcp` server ships in Phase 2 (v0.1.0-demo)
