#!/usr/bin/env bash
# OpsPulse 单命令 — 读单 / 验货 / 结案
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_DIR="${REPO_ROOT}/mcp-server"

usage() {
  cat <<'EOF'
用法:
  ./scripts/opspulse.sh handle --owner OWNER --repo REPO --issue N [--verify]

示例:
  ./scripts/opspulse.sh handle --owner JXzfluser --repo OpsPulse --issue 1 --verify

子命令（直接调 MCP CLI）:
  ./scripts/opspulse.sh parse --owner OWNER --repo REPO --issue-number N
  ./scripts/opspulse.sh trigger pr-validation --owner OWNER --repo REPO
  ./scripts/opspulse.sh status --state deployed --owner OWNER --repo REPO --issue-number N
EOF
}

load_env() {
  if [[ -f "${REPO_ROOT}/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${REPO_ROOT}/.env"
    set +a
  fi
}

cmd="${1:-}"
shift || true
load_env

case "${cmd}" in
  handle)
    owner="" repo="" issue="" verify=0
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --owner) owner="$2"; shift 2 ;;
        --repo) repo="$2"; shift 2 ;;
        --issue) issue="$2"; shift 2 ;;
        --verify) verify=1; shift ;;
        *) echo "未知参数: $1" >&2; exit 1 ;;
      esac
    done
    [[ -n "${owner}" && -n "${repo}" && -n "${issue}" ]] || { usage >&2; exit 1; }

    echo "== 读单 =="
    (cd "${MCP_DIR}" && uv run python -m opspulse_mcp.tools.parse_issue \
      --owner "${owner}" --repo "${repo}" --issue-number "${issue}")

    if [[ "${verify}" -eq 1 ]]; then
      echo
      echo "== 验货 =="
      (cd "${MCP_DIR}" && uv run python -m opspulse_mcp.tools.trigger_pipeline \
        pr-validation --owner "${owner}" --repo "${repo}" --mode github-actions)
    fi
    ;;
  parse)
    (cd "${MCP_DIR}" && uv run python -m opspulse_mcp.tools.parse_issue "$@")
    ;;
  trigger)
    (cd "${MCP_DIR}" && uv run python -m opspulse_mcp.tools.trigger_pipeline "$@")
    ;;
  status)
    (cd "${MCP_DIR}" && uv run python -m opspulse_mcp.tools.update_issue_status "$@")
    ;;
  -h|--help|"")
    usage
    ;;
  *)
    echo "未知命令: ${cmd}" >&2
    usage >&2
    exit 1
    ;;
esac
