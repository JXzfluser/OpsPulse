# OpsPulse 快速入门（约 30 分钟）

本指南演示 **v0.1.0-demo** 本地流程：解析 Issue → 运行流水线 → 生成状态评论。无需 `sample-backend` 或 Java 工具链。

## 前置条件

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 包管理器
- Docker（可选 — 无 Docker 时流水线阶段会优雅跳过）

验证环境：

```bash
./scripts/check-prerequisites.sh
```

## 1. 安装 MCP 服务（约 5 分钟）

```bash
cd mcp-server
uv sync --extra dev
```

在仓库根目录测试 CLI：

```bash
cd mcp-server
uv run python -m opspulse_mcp.tools.parse_issue \
  --file ../examples/issues/001-order-service-feature.md
```

预期输出：JSON 中包含 `"ready": true` 和 `"service": {"name": "order-service", ...}`。

## 2. 解析全部示例 Issue（约 5 分钟）

```bash
uv run python -m opspulse_mcp.tools.parse_issue --file ../examples/issues/001-order-service-feature.md
uv run python -m opspulse_mcp.tools.parse_issue --file ../examples/issues/002-user-service-bugfix.md
uv run python -m opspulse_mcp.tools.parse_issue --file ../examples/issues/003-config-chore.md
```

Issue 002 为 bugfix，含 `## 复现步骤` — 必须解析为 `ready: true`。

## 3. 运行本地流水线（约 10 分钟）

```bash
cd ..   # 回到仓库根目录
export SKIP_BUILD=1
export JDK_BASE_IMAGE=eclipse-temurin:8-jre

./local-runner/run-pipeline.sh pr-validation \
  --issue-file examples/issues/001-order-service-feature.md
```

阶段说明：

1. **validate_spec** — JSON Schema 校验 + bugfix 复现步骤门禁
2. **jdk_base_verify** — `docker pull`（无 Docker 时跳过）
3. **microservice_build** — `SKIP_BUILD=1` 时使用 `examples/fixtures/app.jar`
4. **service_image_build** — 基于 `examples/fixtures/deploy/order-service/Dockerfile` 构建
5. **smoke_test** — `scripts/smoke-test.sh`

## 4. 完整 E2E 演示（约 5 分钟）

```bash
chmod +x scripts/e2e-demo.sh local-runner/run-pipeline.sh scripts/smoke-test.sh
./scripts/e2e-demo.sh
```

## 4b. MCP CLI 辅助命令（可选）

从仓库根目录执行时，需先 `cd mcp-server`，路径相对 `mcp-server/`：

```bash
cd mcp-server

# 状态评论模板（dry-run 仅打印 markdown）
uv run python -m opspulse_mcp.tools.update_issue_status \
  --dry-run --state deployed \
  --service order-service \
  --jdk-base-image eclipse-temurin:8-jre \
  --acceptance-result AC-1:passed

# 通过 local-runner 触发流水线（pipeline_id 为位置参数）
uv run python -m opspulse_mcp.tools.trigger_pipeline \
  pr-validation \
  --issue-file ../examples/issues/001-order-service-feature.md \
  --mode local
```

联调 GitHub 解析（需在 `.env` 中配置 `GITHUB_PAT`）：

```bash
uv run python -m opspulse_mcp.tools.parse_issue \
  --owner JXzfluser --repo OpsPulse --issue-number <N>
```

在 GitHub 上创建带 `opspulse:auto` 标签的 Issue，正文使用 `examples/issues/001-order-service-feature.md` 的 frontmatter，然后将 `<N>` 替换为 Issue 编号。

## 5. 配置 Cursor MCP（约 5 分钟）

确保 `.cursor/mcp.json` 指向 MCP 服务：

```json
"opspulse": {
  "command": "uv",
  "args": ["--directory", "mcp-server", "run", "opspulse-mcp"],
  "env": {
    "OPS_PULSE_CONFIG": "./opspulse.yaml"
  }
}
```

重启 Cursor。Agent 可调用：

- `parse_issue` — 编辑代码前
- `trigger_pipeline` — 打开 PR 后
- `update_issue_status` — 部署完成后

## 6. 运行测试

```bash
cd mcp-server
uv run pytest tests/ -q
```

## 验证清单

在 Cursor 中按以下步骤自检本地环境是否就绪：

1. **重载 Cursor MCP** — 修改 `.cursor/mcp.json` 或 `.env` 后，在 Cursor → Settings → MCP 中确认 `opspulse` 与 `github` 显示已连接；必要时重启 Cursor。
2. **Agent 调用 parse_issue** — 在 Agent 对话中请求解析 `examples/issues/001-order-service-feature.md`，确认返回 `ready: true` 及 `service.name`。
3. **运行 e2e-demo** — 在终端执行 `./scripts/e2e-demo.sh`，确认四步全部通过并输出 `E2E 通过`。
4. **可选：GitHub Issue 联调** — 配置 `GITHUB_PAT` 后，用 `parse_issue --owner ... --repo ... --issue-number N` 解析真实 Issue，或通过 GitHub MCP 搜索 `opspulse:auto` 标签。

## 故障排查

| 现象 | 处理 |
|------|------|
| validate 脚本报 `Missing dependency` | `cd mcp-server && uv sync` |
| Docker 阶段被跳过 | 无 Docker 时为预期行为；E2E 仍可通过 |
| bugfix 解析 `ready: false` | 添加 `## 复现步骤`，或正文中包含「复现/重现」 |
| Cursor 中看不到 MCP | 确认 `uv` 在 PATH 中；必要时对 `--directory` 使用绝对路径 |

## 下一步

- 接入你的微服务仓库（见 [用户接入指南](../doc/用户接入指南.md)）
- 在 Issue frontmatter 中设置企业 `jdk_base_image`
- Phase 3：GitHub webhook 自动触发
