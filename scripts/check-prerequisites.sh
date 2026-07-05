#!/usr/bin/env bash
# OpsPulse Gate 0 prerequisite checker
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PASS=0
FAIL=0
WARN=0

ok() {
  echo "  OK   $1"
  PASS=$((PASS + 1))
}

fail() {
  echo "  FAIL $1"
  FAIL=$((FAIL + 1))
}

warn() {
  echo "  WARN $1"
  WARN=$((WARN + 1))
}

check_cmd() {
  local name="$1"
  local cmd="$2"
  local required="${3:-true}"

  if command -v "${cmd}" >/dev/null 2>&1; then
    local version
    version="$("${cmd}" --version 2>&1 | head -n1 || true)"
    ok "${name}: ${version}"
    return 0
  fi

  if [[ "${required}" == "true" ]]; then
    fail "${name}: '${cmd}' not found"
  else
    warn "${name}: '${cmd}' not found (optional)"
  fi
  return 1
}

check_python_version() {
  if ! command -v python3 >/dev/null 2>&1; then
    fail "Python 3.11+: python3 not found"
    return
  fi

  local version major minor
  version="$(python3 --version 2>&1 | awk '{print $2}')"
  major="$(echo "${version}" | cut -d. -f1)"
  minor="$(echo "${version}" | cut -d. -f2)"

  if [[ "${major}" -ge 3 && "${minor}" -ge 11 ]]; then
    ok "Python 3.11+: ${version}"
  else
    fail "Python 3.11+ required, found ${version}"
  fi
}

check_docker_daemon() {
  if ! command -v docker >/dev/null 2>&1; then
    fail "Docker: docker not found"
    return
  fi

  if docker info >/dev/null 2>&1; then
    ok "Docker daemon: running"
  else
    fail "Docker daemon: not running (start Docker Desktop)"
  fi
}

check_env_file() {
  if [[ -f "${REPO_ROOT}/.env" ]]; then
    ok ".env file exists"
    if grep -qE '^GITHUB_PAT=.+' "${REPO_ROOT}/.env" 2>/dev/null; then
      ok "GITHUB_PAT is set in .env"
    else
      warn "GITHUB_PAT not set in .env (required for MCP)"
    fi
  else
    warn ".env not found — copy from .env.example"
  fi
}

check_schema_validation() {
  if python3 "${REPO_ROOT}/scripts/validate-issue-spec.py" \
    "${REPO_ROOT}/examples/issues/001-order-service-feature.md" >/dev/null 2>&1; then
    ok "Issue Spec validation (example 001)"
  else
    fail "Issue Spec validation failed — pip install jsonschema pyyaml"
  fi
}

echo "OpsPulse prerequisite check"
echo "Repository: ${REPO_ROOT}"
echo

echo "== Required tools =="
check_cmd "Git" git
check_python_version
check_cmd "uv" uv
check_docker_daemon
echo

echo "== Optional tools =="
check_cmd "Node.js" node false
check_cmd "GitHub CLI" gh false
echo

echo "== Configuration =="
check_env_file
if [[ -f "${REPO_ROOT}/opspulse.yaml" ]]; then
  ok "opspulse.yaml present"
else
  fail "opspulse.yaml missing"
fi
echo

echo "== Schema validation =="
if python3 -c "import jsonschema, yaml" 2>/dev/null; then
  ok "Python deps: jsonschema, pyyaml"
  check_schema_validation
else
  warn "Install Python deps: pip install jsonschema pyyaml"
fi
echo

echo "== Summary =="
echo "  Passed:   ${PASS}"
echo "  Failed:   ${FAIL}"
echo "  Warnings: ${WARN}"
echo

if [[ "${FAIL}" -gt 0 ]]; then
  echo "Gate 0: NOT READY — fix failures above"
  exit 1
fi

echo "Gate 0: tools OK (complete interviews and PAT per doc/PREREQUISITES.md)"
exit 0
