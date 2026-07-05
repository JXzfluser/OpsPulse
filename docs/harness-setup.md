# Harness Setup (Optional)

Harness integration is **optional** for MVP. Default CI uses `local-runner/` and GitHub Actions.

## When to use Harness

- Enterprise teams already on Harness CD
- Need Remote Pipeline Templates from Git
- Multi-environment promotion (Pro: staging/prod)

## Repository layout

Copy `harness-templates/` to `.harness/` in your microservice repo (or sync via CI):

```
.harness/
├── templates/
│   ├── stage-validate-spec.yaml
│   ├── stage-jdk-base-verify.yaml
│   ├── stage-microservice-build.yaml
│   ├── stage-service-image-build.yaml
│   ├── stage-deploy-dev.yaml
│   └── stage-smoke-test.yaml
├── pipeline-pr-validation.yaml
└── pipeline-deploy-dev.yaml
```

## Git Connector prerequisites

| Requirement | Detail |
|-------------|--------|
| PAT scopes | `repo`, `admin:repo_hook` |
| API access | Enabled on Harness Git connector |
| Template storage | `.harness/` branch or path in repo |

## Pipeline variables

Map Issue Spec `harness.vars` to pipeline runtime:

| Variable | Source |
|----------|--------|
| `JDK_BASE_IMAGE` | `runtime.jdk_base_image` |
| `SERVICE_NAME` | `service.name` |
| `BUILD_COMMAND` | `build.command` |
| `ARTIFACT_PATH` | `build.artifact` |

## Pipelines

### pr-validation (5 stages)

1. Validate Issue Spec
2. JDK Base Verify (Layer 1)
3. Microservice Build (Layer 2)
4. Service Image Build (Layer 3)
5. Smoke Test

### deploy-dev (5 stages)

1. Build & Package
2. Push Service Image
3. Deploy Dev
4. Smoke Test
5. Update Issue

Phase 1 templates contain **commented placeholders**. Replace `echo` commands when wiring Harness steps.

## Trigger from OpsPulse MCP

Phase 2 `trigger_pipeline` supports `mode=harness`:

```json
{
  "pipeline_id": "pr-validation",
  "mode": "harness",
  "variables": {
    "JDK_BASE_IMAGE": "registry.example.com/platform/jdk8-base:1.0",
    "SERVICE_NAME": "order-service"
  }
}
```

## Local equivalent

| Harness stage | local-runner |
|---------------|--------------|
| validate_spec | `scripts/validate-issue-spec.py` |
| jdk_base_verify | `docker pull $JDK_BASE_IMAGE` |
| microservice_build | `build.command` or `SKIP_BUILD=1` |
| service_image_build | `docker build` |
| deploy_dev | `docker compose up -d` |
| smoke_test | health / acceptance script |

## References

- [技术架构](../doc/技术架构.md) §6
- [Harness Remote Pipeline Templates](https://developer.harness.io/docs/platform/pipelines/harness-yaml-quickstart/)
