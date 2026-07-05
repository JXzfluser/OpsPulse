# MCP 配置指南

配置 Cursor 使用 **github-mcp-server**（官方）与 **opspulse-mcp**（Phase 2）。

## 前置条件

- Docker Desktop 已运行
- Python 3.11 + [uv](https://github.com/astral-sh/uv)
- GitHub PAT，权限范围：`repo`、`workflow`

## 1. 环境变量

```bash
cp .env.example .env
# 编辑 .env：
#   GITHUB_PAT=ghp_...
#   JDK_BASE_IMAGE=eclipse-temurin:8-jre   # 或你的企业镜像
```

切勿提交 `.env`。

## 2. 拉取 github-mcp-server 镜像

```bash
docker pull ghcr.io/github/github-mcp-server
```

## 3. Cursor MCP 配置

将 `.cursor/mcp.json` 复制或软链到项目（或 Cursor 全局 MCP 设置）。

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PAT}"
      }
    },
    "opspulse": {
      "command": "uv",
      "args": ["run", "opspulse-mcp"],
      "env": {
        "OPS_PULSE_CONFIG": "./opspulse.yaml"
      }
    }
  }
}
```

> **Phase 1 说明**：`opspulse-mcp` 在 Phase 2 交付 `mcp-server/` 前为占位；GitHub MCP 可独立测试。

## 4. 验证 GitHub MCP

1. 打开 Cursor → Settings → MCP
2. 确认 `github` 服务显示已连接
3. 测试：在仓库中搜索标签为 `opspulse:auto` 的 Issue

## 5. Agent 规则

启用 `.cursor/rules/issue-to-deploy.mdc`，使 Agent 遵循 parse → code → pipeline 顺序。

## 故障排查

| 现象 | 处理 |
|------|------|
| Docker MCP 无法启动 | 确认 Docker 守护进程运行；重试 `docker pull` |
| PAT 未授权 | 重新生成含 `repo` 权限的 PAT；更新 `.env` |
| 找不到 opspulse 命令 | Phase 1 为预期 — Phase 2 安装 `mcp-server/` |
| Token 未传入容器 | 启动 Cursor 前在 shell 中 export `GITHUB_PAT` |

## 参考

- [github/github-mcp-server](https://github.com/github/github-mcp-server)
- [技术架构](../doc/技术架构.md) §2–3
- [用户接入指南](../doc/用户接入指南.md)
