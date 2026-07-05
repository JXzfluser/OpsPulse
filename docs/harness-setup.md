# Harness 集成（可选）

Harness 为**企业可选** CI 后端，非默认路径。模板位于 `internal/optional/harness-templates/`。

默认验货路径：`trigger_pipeline` → 目标仓 **GitHub Actions**（v0.3.0）。

## 适用场景

团队已使用 Harness，且希望 OpsPulse `trigger_pipeline` 触发 Remote Pipeline。

## 模板位置

```
internal/optional/harness-templates/
├── pipeline-pr-validation.yaml
├── pipeline-deploy-dev.yaml
└── templates/stage-*.yaml
```

在 Harness 控制台导入或同步，**勿**复制进每个微服务业务仓。

## 与 local-runner 对照

| Harness 阶段 | internal/dev/local-runner |
|--------------|---------------------------|
| validate_spec | validate_spec |
| jdk_base_verify | jdk_base_verify |
| microservice_build | microservice_build |
| service_image_build | service_image_build |
| smoke_test | smoke_test |

`internal/dev/local-runner` 仅供 OpsPulse 维护者自测。

## MCP 调用

```json
trigger_pipeline(pipeline_id="pr-validation", mode="harness", ...)
```

`mode=harness` 在 v0.3.0 前未实现；当前仅 `mode=local`（开发自测）。

## 参考

- [Harness Remote Pipeline](https://developer.harness.io/docs/platform/pipelines/harness-yaml-quickstart/)
- [胶水层核心能力](../doc/胶水层核心能力.md)
