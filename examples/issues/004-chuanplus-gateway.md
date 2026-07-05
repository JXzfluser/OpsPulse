---
opspulse_version: "1"
type: feature
scope: config
service:
  name: chuanplus-platform-gateway
  module_path: chuanplus-platform-gateway/
priority: P2
runtime:
  jdk_base_image: prod-ali-pkg.onewo.com/library/vs-docker-public-local/doc-base-docker/jdk:8u202-sec
build:
  tool: maven
  jdk: "1.8"
  command: ./mvnw -pl chuanplus-platform-gateway -am package -DskipTests
  artifact: chuanplus-platform-gateway/target/*.jar
deploy:
  dockerfile: chuanplus-platform-gateway/Dockerfile
  image: prod-ali-pkg.onewo.com/chuanplus/chuanplus-platform-gateway
  tag_strategy: issue-{issue_number}-{git_short_sha}
  env: dev
repository:
  owner: JXzfluser
  name: chuanplus-platform
  ref: main
ci:
  workflow: cicd.yml
  inputs:
    env: test
acceptance:
  - id: AC-1
    given: "gateway 模块构建通过"
    then: "cicd workflow_dispatch 成功触发"
affected_paths:
  - chuanplus-platform-gateway/src/main/java/**
  - chuanplus-platform-gateway/Dockerfile
---

## 背景

OpsPulse 胶水层验证：chuanplus-platform 单体仓 gateway 模块试点。

## 说明

- `repository` + `ci` 指向业务仓已有 `cicd.yml`（workflow_dispatch）
- OpsPulse 不复制任何文件进业务仓
- 验货：`trigger_pipeline pr-validation --owner JXzfluser --repo chuanplus-platform`
