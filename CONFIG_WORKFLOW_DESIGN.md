# OpsPulse 自定义配置工作流设计

> 借鉴 oh-my-config 的 `.omc.json` 理念，为 OpsPulse 引入项目级配置
> 让每个项目有自己的交付流程、CI 策略、部署规则

---

## 一、核心理念

### oh-my-config 做了什么？

```
omc init /path/to/project
  → 扫描项目结构
  → 生成 .omc.json（连接信息、模块列表、环境变量）
  → AI 直接读取配置，写代码自动带连接串
```

**关键洞察：配置是项目级的，不是全局的。**

### OpsPulse 要做什么？

```
opspulse init /path/to/project
  → 扫描项目 CI 配置（GHA/Jenkins/Harness）
  → 生成 .opspulse.yaml（交付流程、策略、规则）
  → handle 自动读取配置，走正确的流程
```

**核心洞察：交付流程是项目级的，不是全局的。**

---

## 二、配置文件设计

### `.opspulse.yaml` — 项目交付配置

```yaml
# 项目标识
project:
  name: order-service
  path: /path/to/project
  modules:
    - gateway
    - web
    - bpm
    - order-service

# 交付流程定义
workflow:
  # 默认阶段
  stages:
    - name: review
      auto: false          # 需要人工确认
      timeout: 3600        # 1 小时超时
    - name: design
      auto: false
      timeout: 7200
    - name: breakdown
      auto: true
      timeout: 3600
    - name: coding
      auto: true
      timeout: 86400       # 24 小时
    - name: pr
      auto: true
      timeout: 3600
    - name: ci
      auto: true
      timeout: 1800        # 30 分钟
    - name: smoke
      auto: true
      timeout: 900         # 15 分钟
    - name: deploy
      auto: false          # 生产环境需要人工确认
      timeout: 3600

# CI 配置
ci:
  # 自动检测到的 CI 后端
  backend: github-actions
  # 或者: jenkins, harness, gitlab-ci
  
  # GHA 配置
  github-actions:
    workflow_file: .github/workflows/cicd.yml
    dispatch_event: workflow_dispatch
    inputs:
      service: "{{ service }}"
      issue_number: "{{ issue_number }}"
      ref: "main"
    
  # 或者 Jenkins 配置
  # jenkins:
  #   url: https://jenkins.example.com
  #   job: order-service-build
  #   credentials_id: jenkins-token
    
  # 或者 Harness 配置
  # harness:
  #   org_id: 12345
  #   project_id: 67890
  #   pipeline_id: order-service-pipeline

# 部署配置
deploy:
  # 环境列表
  environments:
    - name: dev
      type: docker
      auto: true
      health_check: http://localhost:8080/actuator/health
      timeout: 300
      
    - name: staging
      type: docker
      auto: false
      health_check: http://staging.example.com/health
      timeout: 600
      
    - name: prod
      type: kubernetes
      auto: false
      health_check: http://prod.example.com/health
      timeout: 900
      strategy: canary    # 灰度发布
      canary_percentage: 10
      rollback_threshold: 0.01  # 错误率 > 1% 自动回滚

# 策略规则
policies:
  # JDK 底座
  jdk:
    base_image: registry.example.com/platform/jdk8:1.0
    whitelist:
      - registry.example.com/platform/jdk8:*
  
  # 影响路径边界
  affected_paths:
    enforced: true
    allowed_patterns:
      - "order-service/src/**"
      - "order-service/pom.xml"
  
  # 验收标准
  acceptance:
    min_count: 1
    require_given_then: true

# Issue 模板
issue_templates:
  feature:
    title: "feat({service}): {description}"
    frontmatter:
      type: feature
      scope: api
  bugfix:
    title: "fix({service}): {description}"
    frontmatter:
      type: bugfix
      scope: bug
```

---

## 三、与 oh-my-config 的融合

### 对比

| 维度 | oh-my-config | OpsPulse |
|------|-------------|----------|
| **配置内容** | 连接信息、模块列表、环境变量 | 交付流程、CI 策略、部署规则 |
| **配置文件** | `.omc.json` | `.opspulse.yaml` |
| **用途** | AI 写代码时自动带连接串 | AI 交付时自动走正确流程 |
| **扫描** | 扫描项目结构 | 扫描 CI 配置 + 项目结构 |

### 融合方案

```
项目根目录:
├── .omc.json          # 连接信息（oh-my-config）
├── .opspulse.yaml     # 交付流程（OpsPulse）
├── AGENTS.md          # AI 行为规范
├── .github/workflows/ # CI 配置
└── src/               # 业务代码
```

**两个配置文件各司其职：**
- `.omc.json` → AI 写代码时自动带连接串
- `.opspulse.yaml` → AI 交付时自动走正确流程

---

## 四、CLI 命令设计

### 新增命令

```bash
# 1. 初始化项目配置（扫描 CI + 生成 .opspulse.yaml）
opspulse project init /path/to/project

# 2. 查看项目配置
opspulse project show

# 3. 编辑项目配置
opspulse project edit

# 4. 扫描项目，自动检测 CI 后端
opspulse project scan

# 5. 处理 Issue（自动读取 .opspulse.yaml）
opspulse handle --owner myorg --repo myapp --issue 45
```

### 改进后的 handle 流程

```bash
# 没有配置文件的旧方式（需要手动指定）
opspulse handle --owner myorg --repo myapp --issue 45 \
  --mode github-actions \
  --workflow cicd.yml

# 有配置文件的新的方式（自动读取）
opspulse handle --owner myorg --repo myapp --issue 45
# → 自动读取 .opspulse.yaml
# → 自动检测 CI 后端
# → 自动选择正确的 workflow 文件
# → 自动选择正确的部署环境
```

---

## 五、handle 流程改进

### 问题：`--stage all` 太激进

### 改进：分步执行 + 自动确认

```bash
# 方式 1：分步执行（安全）
opspulse handle --issue 45 --stage parse    # 解析 Spec
opspulse handle --issue 45 --stage pr        # 创建 PR（人工审查后）
opspulse handle --issue 45 --stage ci        # 触发 CI
opspulse handle --issue 45 --stage deploy    # 部署（人工确认）

# 方式 2：自动执行 + 关键节点确认
opspulse handle --issue 45 --stage all --auto-parse --auto-ci --confirm-pr --confirm-deploy

# 方式 3：完全自动（信任模式）
opspulse handle --issue 45 --stage all --trust
```

### 基于 `.opspulse.yaml` 的默认行为

```yaml
# .opspulse.yaml 中定义
workflow:
  stages:
    - name: parse
      auto: true          # 自动执行
    - name: pr
      auto: false         # 需要人工确认
    - name: ci
      auto: true          # 自动执行
    - name: deploy
      auto: false         # 需要人工确认
```

用户只需：
```bash
opspulse handle --issue 45
# → 自动执行 parse + ci
# → 暂停等待人工确认 pr
# → 确认后继续
# → 暂停等待人工确认 deploy
# → 确认后完成
```

---

## 六、实现方案

### Phase 1：配置文件生成

```python
# opspulse project init
# 1. 扫描项目根目录
# 2. 检测 CI 配置（.github/workflows/、Jenkinsfile、harness/）
# 3. 扫描项目模块（pom.xml、package.json、Cargo.toml）
# 4. 生成 .opspulse.yaml
```

### Phase 2：handle 自动读取配置

```python
# opspulse handle --issue 45
# 1. 加载 .opspulse.yaml
# 2. 根据 workflow.stages 决定哪些自动执行、哪些需要确认
# 3. 根据 ci.backend 选择正确的 CI 触发方式
# 4. 根据 deploy.environments 选择正确的部署策略
```

### Phase 3：配置编辑

```bash
# opspulse project edit
# → 交互式编辑 .opspulse.yaml
# → 验证配置合法性
# → 热重载配置
```

---

## 七、与 oh-my-config 的互补

| 场景 | oh-my-config | OpsPulse |
|------|-------------|----------|
| AI 写代码 | ✅ 自动带连接串 | ❌ |
| AI 交付 | ❌ | ✅ 自动走正确流程 |
| 配置管理 | ✅ 集中管理连接信息 | ✅ 集中管理交付策略 |
| 审计追踪 | ❌ | ✅ Issue Comment 留痕 |

**两者互补，不冲突。**

---

## 八、文件结构

```
项目根目录:
├── .omc.json          # 连接信息（oh-my-config）
├── .opspulse.yaml     # 交付流程（OpsPulse）← 新增
├── AGENTS.md          # AI 行为规范
├── .github/workflows/ # CI 配置
└── src/               # 业务代码

OpsPulse 仓库:
├── mcp-server/
│   └── src/opspulse_mcp/
│       ├── cli.py                    # CLI 入口
│       ├── project/                  # ← 新增
│       │   ├── scanner.py            # 项目扫描
│       │   ├── generator.py          # 配置生成
│       │   └── loader.py             # 配置加载
│       ├── tools/
│       │   ├── ops_project_init.py   # ← 新增
│       │   ├── ops_project_show.py   # ← 新增
│       │   └── ops_project_edit.py   # ← 新增
│       └── ...
└── schemas/
    ├── issue-spec.v1.json
    └── opspulse-config.v1.json       # ← 新增
```

---

## 九、一句话总结

> **oh-my-config 管「代码怎么写」，OpsPulse 管「交付怎么跑」。
> 两者通过项目级配置文件互补，各自解决不同维度的问题。**
