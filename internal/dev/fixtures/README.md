# OpsPulse Fixtures（维护者）

`internal/dev/` 下演示资产，**不对用户曝光**。无 `sample-backend/`（D11）。

## 用法

```bash
export SKIP_BUILD=1
./scripts/e2e-demo.sh
# 或
./internal/dev/local-runner/run-pipeline.sh pr-validation \
  --issue-file examples/issues/001-order-service-feature.md
```

默认 `ARTIFACT_PATH=internal/dev/fixtures/app.jar`。

## 目录

```
internal/dev/fixtures/
├── app.jar
├── deploy/order-service/Dockerfile
└── README.md
```

用户验货应走 **目标业务仓已有 CI**（v0.3.0 GHA 触发），非本目录。
