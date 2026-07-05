# Pipeline Troubleshoot Prompt

Use when `trigger_pipeline` fails or `internal/dev/local-runner/run-pipeline.sh` exits non-zero.

## Input

- Pipeline: `{{PIPELINE_ID}}` (pr-validation | deploy-dev)
- Failed stage: `{{FAILED_STAGE}}`
- Log excerpt: `{{LOG_SNIPPET}}`
- Issue Spec service: `{{SERVICE_NAME}}`
- JDK base image: `{{JDK_BASE_IMAGE}}`

## Diagnostic checklist

### validate_spec

- Run: `python scripts/validate-issue-spec.py <issue-file>`
- Fix missing frontmatter fields: `service.name`, `runtime.jdk_base_image`, `build.command`, `acceptance`

### jdk_base_verify

- Confirm `docker pull {{JDK_BASE_IMAGE}}` succeeds
- Check registry auth and image tag exists
- For local demo, try `eclipse-temurin:8-jre`

### microservice_build

- Verify JDK 8 and Maven/Gradle on CI agent
- Check `build.command` paths match `service.module_path`
- MVP: set `SKIP_BUILD=1`（维护者自测，见 `internal/dev/fixtures/`）

### service_image_build

- Dockerfile must use `ARG JDK_BASE_IMAGE` + `FROM ${JDK_BASE_IMAGE}`
- Confirm artifact path exists before `COPY`
- Build context must include jar file

### smoke_test

- Container listening on expected port (default 8080)
- Health endpoint: `/actuator/health` or service-specific path
- Review acceptance `given`/`then` in Issue Spec

### deploy_dev

- `docker compose` profile and image tag
- Dev environment variables from Issue (chore type)

### update_issue

- Phase 2: `update_issue_status` requires prior pipeline success
- Include `acceptance_results` with pass/fail per AC id

## Output format

```markdown
## Root cause
<one sentence>

## Fix
1. <action>
2. <action>

## Retry
<command to re-run stage or full pipeline>
```
