# Issue-to-Code Prompt (JDK 8 Microservices)

Use this template when Cursor Agent develops from an OpsPulse Issue.

## Context

You are implementing a change for a **JDK 1.8 microservice** in the user's repository.

**Issue Spec** (from `parse_issue`):

```
{{ISSUE_SPEC_YAML}}
```

**Service**: `{{SERVICE_NAME}}`  
**Module path**: `{{MODULE_PATH}}`  
**JDK base image**: `{{JDK_BASE_IMAGE}}`

## Rules

1. Edit only files matching `affected_paths` in the Issue Spec.
2. Keep Java 8 compatibility — no `var`, modules, or APIs above JDK 8.
3. Build with `{{BUILD_COMMAND}}`; artifact at `{{BUILD_ARTIFACT}}`.
4. Update `deploy/{{SERVICE_NAME}}/Dockerfile` if packaging changes — use `FROM ${JDK_BASE_IMAGE}`.
5. Add or update tests for each acceptance criterion.

## Deliverables

- [ ] Code changes in `{{MODULE_PATH}}`
- [ ] Unit/integration tests covering acceptance criteria
- [ ] Dockerfile still uses enterprise JDK8 base image reference
- [ ] PR description links Issue and lists AC-1, AC-2, …

## Acceptance criteria

{{ACCEPTANCE_LIST}}

## After coding

1. Run local build: `{{BUILD_COMMAND}}` (or note `SKIP_BUILD=1` for config-only chores).
2. Request PR creation via github MCP.
3. Do not mark Issue deployed until pipeline smoke tests pass.
