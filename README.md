# OpsPulse

**仓库：** [github.com/JXzfluser/OpsPulse](https://github.com/JXzfluser/OpsPulse) · 演示标签 [`v0.1.0-demo`](https://github.com/JXzfluser/OpsPulse/releases/tag/v0.1.0-demo)

面向 JDK 1.8 微服务的 **Issue-to-Deploy 脚手架** — 结构化 GitHub Issue、MCP 工具与 CI/CD 流水线模板。

OpsPulse 不替代 Cursor 或你的 JDK8 基础镜像，而是提供 Issue  intake、Agent 开发、构建、部署与状态回写之间的 **契约 + 工作流胶水**。

## 三层交付模型

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: JDK 8 基础镜像（企业运行时）                    │
│  registry.example.com/platform/jdk8-base:1.0            │
└─────────────────────────────────────────────────────────┘
                          ↓ FROM
┌─────────────────────────────────────────────────────────┐
│  Layer 2: 微服务仓库（order-service 等）                 │
│  Maven/Gradle 构建 → jar                                │
└─────────────────────────────────────────────────────────┘
                          ↓ COPY artifact
┌─────────────────────────────────────────────────────────┐
│  Layer 3: 服务镜像 / 部署单元                            │
│  registry.example.com/order-service:issue-45-abc        │
└─────────────────────────────────────────────────────────┘
```

## 快速开始（约 30 秒）

```bash
# 1. 验证环境
./scripts/check-prerequisites.sh

# 2. 校验示例 Issue
python scripts/validate-issue-spec.py examples/issues/001-order-service-feature.md

# 3. 运行流水线骨架（echo 各阶段）
./local-runner/run-pipeline.sh pr-validation --issue-file examples/issues/001-order-service-feature.md
```

复制 `.env.example` → `.env` 并设置 `GITHUB_PAT` 后再进行 MCP 配置（Phase 2）。

完整本地演示见 [快速入门](docs/quickstart.md)。

## 仓库内容（Phase 1–2 MVP）

| 组件 | 路径 | 状态 |
|------|------|------|
| Issue Spec Schema | `schemas/issue-spec.v1.json` | ✅ |
| 示例 Issue | `examples/issues/` | ✅ |
| GitHub Issue 模板 | `.github/ISSUE_TEMPLATE/` | ✅ |
| Schema CI | `.github/workflows/validate-schema.yml` | ✅ |
| 流水线骨架 | `harness-templates/`, `local-runner/` | ✅ 占位 |
| MCP 服务 | `mcp-server/` | ✅ |

> **无 `sample-backend/`** — 演示使用 `examples/issues/` + `examples/fixtures/`（D11）。

## 文档

| 文档 | 说明 |
|------|------|
| [用户接入指南](doc/用户接入指南.md) | 如何将模板 fork 到微服务仓库 |
| [技术架构](doc/技术架构.md) | MCP、Issue 解析、Harness 阶段 |
| [实施计划](doc/实施计划.md) | Phase 0–2 执行计划 |
| [MCP 配置](docs/mcp-setup.md) | Cursor + github-mcp-server 配置 |
| [快速入门](docs/quickstart.md) | 本地 E2E 与验证清单 |
| [Harness 配置](docs/harness-setup.md) | 可选的企业 CI/CD 集成 |

## 架构流程

```
GitHub Issue (opspulse:auto)
    → parse_issue (MCP)
    → Cursor Agent + prompts/issue-to-code.md
    → PR + trigger_pipeline (pr-validation)
    → deploy-dev
    → update_issue_status (Comment)
```

## License

Apache License 2.0 — 见 [LICENSE](LICENSE)。

## Contributing

见 [CONTRIBUTING.md](CONTRIBUTING.md)。
