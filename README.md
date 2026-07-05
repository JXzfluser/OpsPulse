# OpsPulse

**Repository:** [github.com/JXzfluser/OpsPulse](https://github.com/JXzfluser/OpsPulse) · Demo tag [`v0.1.0-demo`](https://github.com/JXzfluser/OpsPulse/releases/tag/v0.1.0-demo)

**Issue-to-Deploy scaffold** for JDK 1.8 microservices — structured GitHub Issues, MCP tools, and CI/CD pipeline templates.

OpsPulse does not replace Cursor or your JDK8 base image. It provides the **contract + workflow glue** between Issue intake, Agent development, build, deploy, and status feedback.

## Three-layer delivery model

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: JDK 8 base image (enterprise runtime)         │
│  registry.example.com/platform/jdk8-base:1.0            │
└─────────────────────────────────────────────────────────┘
                          ↓ FROM
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Microservice repo (order-service, etc.)       │
│  Maven/Gradle build → jar                               │
└─────────────────────────────────────────────────────────┘
                          ↓ COPY artifact
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Service image / deploy unit                   │
│  registry.example.com/order-service:issue-45-abc        │
└─────────────────────────────────────────────────────────┘
```

## Quick start (30 seconds)

```bash
# 1. Verify environment
./scripts/check-prerequisites.sh

# 2. Validate an example Issue
python scripts/validate-issue-spec.py examples/issues/001-order-service-feature.md

# 3. Run pipeline skeleton (echo stages)
./local-runner/run-pipeline.sh pr-validation --issue-file examples/issues/001-order-service-feature.md
```

Copy `.env.example` → `.env` and set `GITHUB_PAT` before MCP setup (Phase 2).

## What's in this repo (Phase 1–2 MVP)

| Component | Path | Status |
|-----------|------|--------|
| Issue Spec Schema | `schemas/issue-spec.v1.json` | ✅ |
| Example Issues | `examples/issues/` | ✅ |
| GitHub Issue templates | `.github/ISSUE_TEMPLATE/` | ✅ |
| Schema CI | `.github/workflows/validate-schema.yml` | ✅ |
| Pipeline skeleton | `harness-templates/`, `local-runner/` | ✅ placeholder |
| MCP server | `mcp-server/` | ✅ |

> **No `sample-backend/`** — demo uses `examples/issues/` + `examples/fixtures/` (D11).

## Documentation

| Doc | Description |
|-----|-------------|
| [用户接入指南](doc/用户接入指南.md) | How to fork templates into your microservice repo |
| [技术架构](doc/技术架构.md) | MCP, Issue parsing, Harness stages |
| [实施计划](doc/实施计划.md) | Phase 0–2 execution plan |
| [MCP setup](docs/mcp-setup.md) | Cursor + github-mcp-server configuration |
| [Harness setup](docs/harness-setup.md) | Optional enterprise CI/CD integration |

## Architecture flow

```
GitHub Issue (opspulse:auto)
    → parse_issue (MCP)
    → Cursor Agent + prompts/issue-to-code.md
    → PR + trigger_pipeline (pr-validation)
    → deploy-dev
    → update_issue_status (Comment)
```

## License

Apache License 2.0 — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
