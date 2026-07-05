#!/usr/bin/env bash
# OpsPulse local-runner — pr-validation and deploy-dev pipelines
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
DEV_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PIPELINE=""
ISSUE_FILE=""
PR_NUMBER=""
ISSUE_NUMBER=""

usage() {
  cat <<'EOF'
Usage: run-pipeline.sh <pr-validation|deploy-dev> [options]

Options:
  --issue-file PATH   Issue markdown file (for validate_spec stage)
  --pr NUMBER         Pull request number (optional)
  --issue NUMBER      GitHub issue number (optional)

Environment:
  JDK_BASE_IMAGE      Layer 1 JDK8 base image (default: eclipse-temurin:8-jre)
  SERVICE_NAME        Microservice name
  SKIP_BUILD          Set to 1 to skip Maven build (MVP fixture mode)
  ARTIFACT_PATH       Path to jar when SKIP_BUILD=1
  DOCKERFILE_PATH     Service Dockerfile path (default: internal/dev/fixtures/deploy/order-service/Dockerfile)
  BUILD_CONTEXT       Docker build context (default: internal/dev/fixtures)
EOF
}

emit_stage() {
  local name="$1"
  local status="$2"
  local message="${3:-}"
  echo "OPS_STAGE:${name}:${status}:${message}"
}

log_stage() {
  echo "==> [${1}] ${2}"
}

docker_available() {
  command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    pr-validation|deploy-dev)
      PIPELINE="$1"
      shift
      ;;
    --issue-file)
      ISSUE_FILE="$2"
      shift 2
      ;;
    --pr)
      PR_NUMBER="$2"
      shift 2
      ;;
    --issue)
      ISSUE_NUMBER="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${PIPELINE}" ]]; then
  echo "Pipeline name required." >&2
  usage >&2
  exit 1
fi

JDK_BASE_IMAGE="${JDK_BASE_IMAGE:-eclipse-temurin:8-jre}"
SERVICE_NAME="${SERVICE_NAME:-order-service}"
SKIP_BUILD="${SKIP_BUILD:-1}"
ARTIFACT_PATH="${ARTIFACT_PATH:-${DEV_ROOT}/fixtures/app.jar}"
DOCKERFILE_PATH="${DOCKERFILE_PATH:-${DEV_ROOT}/fixtures/deploy/order-service/Dockerfile}"
BUILD_CONTEXT="${BUILD_CONTEXT:-${DEV_ROOT}/fixtures}"

echo "OpsPulse local-runner"
echo "  pipeline: ${PIPELINE}"
echo "  jdk_base_image: ${JDK_BASE_IMAGE}"
echo "  service: ${SERVICE_NAME}"
[[ -n "${ISSUE_FILE}" ]] && echo "  issue_file: ${ISSUE_FILE}"
[[ -n "${PR_NUMBER}" ]] && echo "  pr: ${PR_NUMBER}"
[[ -n "${ISSUE_NUMBER}" ]] && echo "  issue: ${ISSUE_NUMBER}"
echo

stage_validate_spec() {
  log_stage "validate_spec" "Validating Issue Spec"
  if [[ -n "${ISSUE_FILE}" ]]; then
    if python3 "${REPO_ROOT}/scripts/validate-issue-spec.py" "${ISSUE_FILE}"; then
      emit_stage "validate_spec" "success" "schema valid"
    else
      emit_stage "validate_spec" "failed" "schema validation failed"
      return 1
    fi
  else
    echo "  (skipped — no --issue-file provided)"
    emit_stage "validate_spec" "skipped" "no issue file"
  fi
}

stage_jdk_base_verify() {
  log_stage "jdk_base_verify" "Verify JDK8 base image: ${JDK_BASE_IMAGE}"
  if docker_available; then
    if docker pull "${JDK_BASE_IMAGE}"; then
      emit_stage "jdk_base_verify" "success" "pulled ${JDK_BASE_IMAGE}"
    else
      emit_stage "jdk_base_verify" "failed" "docker pull failed"
      return 1
    fi
  else
    echo "  docker not available — skipping pull"
    emit_stage "jdk_base_verify" "skipped" "docker not available"
  fi
}

stage_microservice_build() {
  log_stage "microservice_build" "Build microservice: ${SERVICE_NAME}"
  if [[ "${SKIP_BUILD}" == "1" ]]; then
    if [[ ! -f "${ARTIFACT_PATH}" ]]; then
      echo "  creating placeholder artifact: ${ARTIFACT_PATH}"
      mkdir -p "$(dirname "${ARTIFACT_PATH}")"
      python3 - <<'PY' "${ARTIFACT_PATH}"
import sys
import zipfile
from pathlib import Path

path = Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(path, "w") as jar:
    jar.writestr(
        "META-INF/MANIFEST.MF",
        "Manifest-Version: 1.0\nCreated-By: OpsPulse\n\n",
    )
PY
    fi
    echo "  SKIP_BUILD=1 — using fixture: ${ARTIFACT_PATH}"
    if [[ "${ARTIFACT_PATH}" != "${BUILD_CONTEXT}/app.jar" ]]; then
      cp "${ARTIFACT_PATH}" "${BUILD_CONTEXT}/app.jar"
    fi
    emit_stage "microservice_build" "success" "fixture artifact ready"
  else
    # Try real Maven build
    if command -v mvn >/dev/null 2>&1; then
      # Look for pom.xml in common locations
      local pom_found=""
      local build_dir="${PWD}"
      if [[ -f "pom.xml" ]]; then
        pom_found="."
      elif [[ -f "${ARTIFACT_PATH%/target/*}/pom.xml" ]]; then
        pom_found="$(dirname "${ARTIFACT_PATH%/target/*}")"
      fi

      if [[ -n "${pom_found}" ]]; then
        echo "  Found pom.xml at: ${pom_found}"
        echo "  Running: mvn clean package -DskipTests"
        (cd "${pom_found}" && mvn clean package -DskipTests -q) 2>&1
        if [[ $? -eq 0 ]]; then
          # Copy artifact to expected location
          local jar_name="${SERVICE_NAME}.jar"
          local target_dir="${ARTIFACT_PATH%/target/*}/target"
          if [[ -f "${target_dir}/${jar_name}" ]]; then
            mkdir -p "$(dirname "${ARTIFACT_PATH}")"
            cp "${target_dir}/${jar_name}" "${ARTIFACT_PATH}"
            emit_stage "microservice_build" "success" "maven build passed (${jar_name})"
          else
            emit_stage "microservice_build" "failed" "jar not found at ${target_dir}/${jar_name}"
            return 1
          fi
        else
          emit_stage "microservice_build" "failed" "maven build failed"
          return 1
        fi
      else
        echo "  No pom.xml found — falling back to fixture"
        # Create placeholder
        mkdir -p "$(dirname "${ARTIFACT_PATH}")"
        python3 - <<'PY' "${ARTIFACT_PATH}"
import sys, zipfile
from pathlib import Path
path = Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(path, "w") as jar:
    jar.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nCreated-By: OpsPulse\n\n")
PY
        emit_stage "microservice_build" "success" "fixture fallback"
      fi
    else
      echo "  mvn not found — using fixture artifact"
      mkdir -p "$(dirname "${ARTIFACT_PATH}")"
      python3 - <<'PY' "${ARTIFACT_PATH}"
import sys, zipfile
from pathlib import Path
path = Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(path, "w") as jar:
    jar.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\nCreated-By: OpsPulse\n\n")
PY
      emit_stage "microservice_build" "success" "fixture (no maven)"
    fi
  fi
}

stage_service_image_build() {
  log_stage "service_image_build" "Build service image FROM ${JDK_BASE_IMAGE}"
  if docker_available; then
    if docker build \
      -f "${DOCKERFILE_PATH}" \
      --build-arg "JDK_BASE_IMAGE=${JDK_BASE_IMAGE}" \
      -t "opspulse/${SERVICE_NAME}:local" \
      "${BUILD_CONTEXT}"; then
      emit_stage "service_image_build" "success" "opspulse/${SERVICE_NAME}:local"
    else
      emit_stage "service_image_build" "failed" "docker build failed"
      return 1
    fi
  else
    echo "  docker not available — skipping image build"
    emit_stage "service_image_build" "skipped" "docker not available"
  fi
}

stage_smoke_test() {
  log_stage "smoke_test" "Run smoke test"
  if OPSPULSE_SERVICE_IMAGE="opspulse/${SERVICE_NAME}:local" \
     OPSPULSE_JDK_BASE_IMAGE="${JDK_BASE_IMAGE}" \
     OPSPULSE_ARTIFACT_PATH="${ARTIFACT_PATH}" \
     bash "${DEV_ROOT}/smoke-test.sh"; then
    emit_stage "smoke_test" "success" "smoke checks passed"
  else
    emit_stage "smoke_test" "failed" "smoke checks failed"
    return 1
  fi
}

run_pr_validation() {
  stage_validate_spec
  stage_jdk_base_verify
  stage_microservice_build
  stage_service_image_build
  stage_smoke_test
}

run_deploy_dev() {
  log_stage "build_package" "Build and package ${SERVICE_NAME}"
  stage_microservice_build

  log_stage "push_service_image" "Push service image"
  if docker_available; then
    echo "  (local demo — skip registry push)"
    emit_stage "push_service_image" "skipped" "local demo"
  else
    emit_stage "push_service_image" "skipped" "docker not available"
  fi

  log_stage "deploy_dev" "Deploy to Dev environment"
  if docker_available; then
    echo "  docker compose profile demo available at ${SCRIPT_DIR}/docker-compose.yml"
    emit_stage "deploy_dev" "skipped" "compose deploy optional in MVP"
  else
    emit_stage "deploy_dev" "skipped" "docker not available"
  fi

  stage_smoke_test

  log_stage "update_issue" "Update Issue status"
  echo "  update_issue_status(state=deployed) — run via MCP tool"
  emit_stage "update_issue" "success" "dry-run only in local-runner"
}

case "${PIPELINE}" in
  pr-validation)
    run_pr_validation
    ;;
  deploy-dev)
    run_deploy_dev
    ;;
esac

echo
echo "Pipeline '${PIPELINE}' completed."
