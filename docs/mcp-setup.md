# MCP Setup

Configure Cursor to use **github-mcp-server** (official) and **opspulse-mcp** (Phase 2).

## Prerequisites

- Docker Desktop running
- Python 3.11 + [uv](https://github.com/astral-sh/uv)
- GitHub PAT with scopes: `repo`, `workflow`

## 1. Environment variables

```bash
cp .env.example .env
# Edit .env:
#   GITHUB_PAT=ghp_...
#   JDK_BASE_IMAGE=eclipse-temurin:8-jre   # or your enterprise image
```

Never commit `.env`.

## 2. Pull github-mcp-server image

```bash
docker pull ghcr.io/github/github-mcp-server
```

## 3. Cursor MCP config

Copy or symlink `.cursor/mcp.json` to your project (or global Cursor MCP settings).

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

> **Phase 1 note**: `opspulse-mcp` is a placeholder until `mcp-server/` ships in Phase 2. GitHub MCP can be tested independently.

## 4. Verify GitHub MCP

1. Open Cursor → Settings → MCP
2. Confirm `github` server shows connected
3. Test: search issues with label `opspulse:auto` in your repo

## 5. Agent rules

Enable `.cursor/rules/issue-to-deploy.mdc` so Agent follows parse → code → pipeline order.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Docker MCP won't start | Ensure Docker daemon is running; retry `docker pull` |
| PAT unauthorized | Regenerate PAT with `repo` scope; update `.env` |
| opspulse command not found | Expected in Phase 1 — install `mcp-server/` in Phase 2 |
| Token not passed to container | Export `GITHUB_PAT` in shell before launching Cursor |

## References

- [github/github-mcp-server](https://github.com/github/github-mcp-server)
- [技术架构](../doc/技术架构.md) §2–3
- [用户接入指南](../doc/用户接入指南.md)
