---
opspulse_version: "1"
type: feature
scope: api
service:
  name: order-service
  module_path: services/order-service/
priority: P1
runtime:
  jdk_base_image: registry.example.com/platform/jdk8-base:1.0
build:
  tool: maven
  jdk: "1.8"
  command: mvn -pl services/order-service -am package -DskipTests
  artifact: services/order-service/target/order-service.jar
deploy:
  dockerfile: deploy/order-service/Dockerfile
  image: registry.example.com/order-service
  tag_strategy: issue-{issue_number}-{git_short_sha}
  env: dev
harness:
  pipeline: pr-validation
  vars:
    JDK_BASE_IMAGE: registry.example.com/platform/jdk8-base:1.0
    SERVICE_NAME: order-service
acceptance:
  - id: AC-1
    given: "order-service 使用 JDK8 基础镜像构建并启动"
    then: "GET /actuator/health 返回 UP"
  - id: AC-2
    given: "本次 Issue 的 API 变更已部署 Dev"
    then: "POST /api/orders 返回 201"
affected_paths:
  - services/order-service/src/main/java/**
  - services/order-service/src/test/java/**
  - deploy/order-service/Dockerfile
---

## 背景

为 order-service 新增创建订单 API，供 Dev 环境验收。本 Issue 演示 OpsPulse 三层交付模型：JDK8 基础镜像 → 微服务 build → 服务镜像部署。

## 实现提示

- 使用现有 `OrderController` 扩展端点
- Dockerfile 保持 `FROM ${JDK_BASE_IMAGE}` 模式
- 验收以 Dev 环境 `/actuator/health` 与 API 行为为准
