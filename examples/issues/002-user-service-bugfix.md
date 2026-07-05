---
opspulse_version: "1"
type: bugfix
scope: api
service:
  name: user-service
  module_path: services/user-service/
priority: P0
runtime:
  jdk_base_image: registry.example.com/platform/jdk8-base:1.0
build:
  tool: maven
  jdk: "1.8"
  command: mvn -pl services/user-service -am package -DskipTests
  artifact: services/user-service/target/user-service.jar
deploy:
  dockerfile: deploy/user-service/Dockerfile
  image: registry.example.com/user-service
  tag_strategy: issue-{issue_number}-{git_short_sha}
  env: dev
harness:
  pipeline: pr-validation
  vars:
    JDK_BASE_IMAGE: registry.example.com/platform/jdk8-base:1.0
    SERVICE_NAME: user-service
acceptance:
  - id: AC-1
    given: "user-service 使用修复后代码构建并启动"
    then: "POST /api/login 空密码不再抛出 NPE，返回 400"
affected_paths:
  - services/user-service/src/main/java/**
  - services/user-service/src/test/java/**
---

## 背景

线上 user-service 在用户登录时，空密码触发 `NullPointerException`，导致 500 错误。

## 复现步骤

1. 部署当前 Dev 环境 user-service
2. `POST /api/login` body: `{"username":"demo","password":""}`
3. 观察响应为 500，日志含 `NullPointerException` at `AuthService.validatePassword`

## 实现提示

- 在 `AuthService` 入口增加空值校验
- 补充单元测试覆盖空密码场景
