# Internal — 维护者专用

用户路径见 [docs/getting-started.md](../docs/getting-started.md)。本目录不对业务仓暴露。

| 路径 | 用途 |
|------|------|
| `dev/local-runner/` | MCP `trigger_pipeline` 的 `mode=local` 后端（开发自测） |
| `dev/fixtures/` | 无 Java 后端时的占位 jar + Dockerfile（D11） |
| `dev/smoke-test.sh` | local-runner 冒烟阶段 |
| `optional/harness-templates/` | 企业 Harness 可选适配 |

生产路径：`trigger_pipeline` → 客户 **GHA `workflow_dispatch`**（P0 待实现）。
