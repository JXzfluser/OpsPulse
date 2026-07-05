---
opspulse_version: "1"
type: chore
scope: config
service:
  name: order-service
  module_path: services/order-service/
priority: P2
runtime:
  jdk_base_image: registry.example.com/platform/jdk8-base:1.0
build:
  tool: maven
  jdk: "1.8"
  command: echo "skip build for config-only change"
  artifact: services/order-service/target/order-service.jar
deploy:
  dockerfile: deploy/order-service/Dockerfile
  image: registry.example.com/order-service
  tag_strategy: issue-{issue_number}-{git_short_sha}
  env: dev
harness:
  pipeline: deploy-dev
  vars:
    JDK_BASE_IMAGE: registry.example.com/platform/jdk8-base:1.0
    SERVICE_NAME: order-service
acceptance:
  - id: AC-1
    given: "order-service Dev 部署使用新环境变量 LOG_LEVEL=DEBUG"
    then: "启动日志包含 DEBUG 级别输出"
affected_paths:
  - deploy/order-service/docker-compose.override.yml
  - services/order-service/src/main/resources/application-dev.yml
---

## 背景

仅调整 order-service Dev 环境日志级别，无需代码逻辑变更。流水线可跳过完整 Maven build，仅更新配置并重新部署。

## 实现提示

- 修改 `application-dev.yml` 中 `logging.level.root`
- 更新 compose override 中的环境变量
- 使用 `SKIP_BUILD=1` 时以现有 artifact 打镜像
