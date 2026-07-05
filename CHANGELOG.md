# Changelog

All notable changes to OpsPulse are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] — v0.3.0 真 CI

### Added

- `trigger_pipeline` **`mode=github-actions`** — `workflow_dispatch` 触发目标仓已有 CI
- Issue Spec 可选字段：`repository`、`ci`
- `opspulse.yaml` → `pipeline.github_actions.repositories` 映射（含 chuanplus `cicd.yml` 示例）
- `update_issue_status` 支持 **post GitHub Issue Comment**（`--owner --repo --issue-number`）
- `scripts/opspulse.sh` — `handle` / `parse` / `trigger` / `status` 单入口
- `.github/workflows/opspulse-pr-validation.yml` — OpsPulse 仓可 dispatch 演示 workflow
- `examples/issues/004-chuanplus-gateway.md` — 零侵入业务仓试点样例

## [Unreleased] — v0.2.0 胶水收敛

### Added

- `doc/胶水层核心能力.md` — 产品北极星（三动词 + 四引擎）
- `docs/getting-started.md` — 唯一用户上手文档
- `internal/README.md` — 维护者自测说明

### Changed

- **BREAKING（布局）**：`local-runner/`、`fixtures/` → `internal/dev/`；`harness-templates/` → `internal/optional/`
- README 重写：三动词入口，业务仓零侵入
- `doc/ROADMAP.md` 按 v0.2–v1.0 真胶水路径重规划
- D4 决策修订：默认 CI 为 GHA，local-runner 仅维护者自测

### Removed

- `scripts/bootstrap-to-repo.sh`、`scripts/onboard-local.sh`、`scripts/remove-bootstrap.sh`
- `docs/quickstart.md`、`docs/本地接入引导.md`（合并入 getting-started）
- 规划文档移至 `doc/internal/`

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
