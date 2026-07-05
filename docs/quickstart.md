# OpsPulse Quickstart (30 minutes)

This guide walks through the **v0.1.0-demo** local flow: parse an Issue → run pipelines → generate a status comment. No `sample-backend` or Java toolchain required.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (optional — pipeline stages skip gracefully without it)

Verify:

```bash
./scripts/check-prerequisites.sh
```

## 1. Install MCP server (5 min)

```bash
cd mcp-server
uv sync --extra dev
```

From repo root, test the CLI:

```bash
cd mcp-server
uv run python -m opspulse_mcp.tools.parse_issue \
  --file ../examples/issues/001-order-service-feature.md
```

Expected: JSON with `"ready": true` and `"service": {"name": "order-service", ...}`.

## 2. Parse all example Issues (5 min)

```bash
uv run python -m opspulse_mcp.tools.parse_issue --file ../examples/issues/001-order-service-feature.md
uv run python -m opspulse_mcp.tools.parse_issue --file ../examples/issues/002-user-service-bugfix.md
uv run python -m opspulse_mcp.tools.parse_issue --file ../examples/issues/003-config-chore.md
```

Issue 002 is a bugfix with `## 复现步骤` — it must parse as `ready: true`.

## 3. Run local pipeline (10 min)

```bash
cd ..   # repo root
export SKIP_BUILD=1
export JDK_BASE_IMAGE=eclipse-temurin:8-jre

./local-runner/run-pipeline.sh pr-validation \
  --issue-file examples/issues/001-order-service-feature.md
```

Stages:

1. **validate_spec** — JSON Schema + bugfix reproduction gate
2. **jdk_base_verify** — `docker pull` (skipped if Docker unavailable)
3. **microservice_build** — uses `examples/fixtures/app.jar` when `SKIP_BUILD=1`
4. **service_image_build** — builds from `examples/fixtures/deploy/order-service/Dockerfile`
5. **smoke_test** — `scripts/smoke-test.sh`

## 4. Full E2E demo (5 min)

```bash
chmod +x scripts/e2e-demo.sh local-runner/run-pipeline.sh scripts/smoke-test.sh
./scripts/e2e-demo.sh
```

## 5. Wire Cursor MCP (5 min)

Ensure `.cursor/mcp.json` points at the MCP server:

```json
"opspulse": {
  "command": "uv",
  "args": ["--directory", "mcp-server", "run", "opspulse-mcp"],
  "env": {
    "OPS_PULSE_CONFIG": "./opspulse.yaml"
  }
}
```

Restart Cursor. The Agent can call:

- `parse_issue` — before editing code
- `trigger_pipeline` — after opening a PR
- `update_issue_status` — after deploy

## 6. Run tests

```bash
cd mcp-server
uv run pytest tests/ -q
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Missing dependency` in validate script | `cd mcp-server && uv sync` |
| Docker stages skipped | Expected without Docker; E2E still passes |
| `ready: false` on bugfix | Add `## 复现步骤` or include 复现/重现 in body |
| MCP not listed in Cursor | Check `uv` on PATH; use absolute `--directory` if needed |

## Next steps

- Connect your microservice repo (see [用户接入指南](../doc/用户接入指南.md))
- Set enterprise `jdk_base_image` in Issue frontmatter
- Phase 3: GitHub webhook auto-trigger
