#!/usr/bin/env bash
# OpsPulse Gate 2 E2E demo — parse → pr-validation → deploy-dev → update_issue_status
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

ISSUE_FILE="${ISSUE_FILE:-examples/issues/001-order-service-feature.md}"
MCP_DIR="${REPO_ROOT}/mcp-server"

echo "== 1. parse_issue =="
(cd "${MCP_DIR}" && uv run python -m opspulse_mcp.tools.parse_issue --file "../${ISSUE_FILE}")

echo
echo "== 2. pr-validation =="
./local-runner/run-pipeline.sh pr-validation --issue-file "${ISSUE_FILE}"

echo
echo "== 3. deploy-dev =="
./local-runner/run-pipeline.sh deploy-dev --issue-file "${ISSUE_FILE}"

echo
echo "== 4. update_issue_status (dry-run) =="
(cd "${MCP_DIR}" && uv run python -m opspulse_mcp.tools.update_issue_status \
  --dry-run \
  --state deployed \
  --service order-service \
  --jdk-base-image eclipse-temurin:8-jre \
  --acceptance-result AC-1:passed \
  --acceptance-result AC-2:failed)

echo
echo "E2E PASSED"
