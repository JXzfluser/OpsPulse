# Contributing to OpsPulse

胶水层开源项目 — 贡献前请读 [胶水层核心能力](doc/胶水层核心能力.md)。

## 开发环境

```bash
./scripts/check-prerequisites.sh
cp .env.example .env   # 勿提交 .env
cd mcp-server && uv sync --extra dev
```

## Issue / PR

- 使用 `.github/ISSUE_TEMPLATE/` 模板，frontmatter 符合 `schemas/issue-spec.v1.json`
- bugfix 必须含 `## 复现步骤`
- 校验：`python scripts/validate-issue-spec.py examples/issues/001-order-service-feature.md`
- 勿向本仓添加 `sample-backend/`（D11）

## 仓库布局

| 路径 | 用途 |
|------|------|
| `mcp-server/` | 核心 MCP（三 Tool） |
| `schemas/` | Issue Spec |
| `examples/issues/` | 参考工单 |
| `prompts/` | Agent 指令 |
| `internal/dev/` | 维护者自测（local-runner、fixtures） |
| `internal/optional/` | Harness 可选模板 |
| `docs/getting-started.md` | **唯一用户上手文档** |

## 自测

```bash
./scripts/e2e-demo.sh
cd mcp-server && uv run pytest tests/ -q
```

## 问题

GitHub Issue 标签 `question`，或查阅 `doc/internal/实施计划.md`。
