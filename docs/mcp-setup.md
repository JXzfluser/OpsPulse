# MCP 配置

一次性配置，之后日常只用三个动词。见 [快速上手](./getting-started.md)。

## 前置

- Docker（github-mcp-server）
- Python 3.11 + `uv`
- `GITHUB_PAT`（`repo`, `workflow`）

```bash
cp .env.example .env
cd mcp-server && uv sync --extra dev
docker pull ghcr.io/github/github-mcp-server
```

## Cursor 配置

使用本仓 `.cursor/mcp.json`：

```json
"opspulse": {
  "command": "uv",
  "args": ["--directory", "mcp-server", "run", "opspulse-mcp"],
  "env": { "OPS_PULSE_CONFIG": "./opspulse.yaml" }
}
```

重载 Cursor → Settings → MCP → 确认 **github** / **opspulse** 已连接。

## 验证

```
请用 parse_issue 解析 examples/issues/001-order-service-feature.md
```

预期：`ready: true`。

## 业务仓

MCP 配置在 **OpsPulse 仓或用户级**；打开业务仓写代码时，MCP 仍可用（绝对路径指向 `mcp-server`）。

## 故障排查

| 现象 | 处理 |
|------|------|
| opspulse 未连接 | `uv` 在 PATH；`cd mcp-server && uv sync` |
| github 未连接 | Docker 运行；PAT 在 `.env` |
| Token 未传入 | 启动 Cursor 前 `set -a && source .env && set +a` |
