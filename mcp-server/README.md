# OpsPulse MCP Server

Python FastMCP server exposing three tools for Issue-to-Deploy workflows.

## Tools

| Tool | Description |
|------|-------------|
| `parse_issue` | Parse Issue Spec from GitHub or local markdown file |
| `trigger_pipeline` | 编排 CI（`mode=local` → `internal/dev/local-runner`；v0.3 GHA） |
| `update_issue_status` | Generate structured Issue comment markdown |

## Quick start

```bash
cd mcp-server
uv sync --extra dev

# MCP server (stdio)
uv run opspulse-mcp

# CLI helpers
uv run python -m opspulse_mcp.tools.parse_issue --file ../examples/issues/001-order-service-feature.md
uv run python -m opspulse_mcp.tools.update_issue_status --dry-run --state deployed
uv run pytest tests/ -q
```

Set `OPS_PULSE_CONFIG` to point at repo-root `opspulse.yaml` (default: `./opspulse.yaml`).
