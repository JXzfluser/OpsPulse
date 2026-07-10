# OpsPulse — Pure CLI Glue Layer

> 独立于 MCP / AI Agent，纯命令行 Issue-to-Deploy 交付闭环
> 项目级配置 + 标准化工作流 + 高效胶水命令

---

## 设计理念

**胶水层的价值公式：**

```
胶水价值 = （契约可执行 + 策略可强制 + 交付可验证 + 结果可审计）− （多出来的操作成本）
```

**核心原则：**
1. 每个命令只做一件事，组合起来就是完整流水线
2. 配置在项目根目录，一次扫描，处处可用
3. 不依赖 MCP、不依赖 AI Agent、不依赖 Docker
4. GitHub API 是唯一外部依赖

---

## 命令体系

### 核心命令（4 个）

```bash
# 1. 创建 Issue
opspulse new --owner myorg --repo myapp --title "Add refund API" \
  --service order-service --type feature

# 2. 处理 Issue（核心胶水命令）
opspulse handle --owner myorg --repo myapp --issue 45

# 3. 评审 Issue
opspulse review --owner myorg --repo myapp --issue 45

# 4. 查看交付日志
opspulse log --owner myorg --repo myapp --issue 45
```

### 管理命令

```bash
# 项目扫描 + 配置生成
opspulse project init /path/to/project
opspulse project show

# Issue 状态查询
opspulse status --owner myorg --repo myapp --issue 45
```

---

## handle 命令详解

`handle` 是胶水层的核心，它串联整个交付流程：

```bash
opspulse handle --owner myorg --repo myapp --issue 45
```

### 内部流程

```
1. 拉取 Issue #45
   ↓
2. 解析 Spec（从 frontmatter 或 Comment）
   ↓
3. 验证 Spec（Schema 校验）
   ↓
4. 创建分支 + PR
   ↓
5. 触发 CI（GHA / Jenkins / Harness）
   ↓
6. 回写 Issue Comment（状态 + 验收）
```

### 分步执行

```bash
# 只解析 Spec
opspulse handle --issue 45 --step parse

# 只创建 PR
opspulse handle --issue 45 --step pr

# 只触发 CI
opspulse handle --issue 45 --step ci

# 只回写状态
opspulse handle --issue 45 --step status

# 完整流水线
opspulse handle --issue 45 --step all
```

---

## 项目配置

### `.opspulse.yaml` — 项目交付配置

```yaml
# 自动生成，勿手动编辑
# 使用 opspulse project init 生成
# 使用 opspulse project edit 编辑

project:
  name: order-service
  modules: [gateway, web, bpm, order-service]
  languages: [java]

ci:
  backend: github-actions
  github-actions:
    workflow_file: .github/workflows/cicd.yml
    dispatch_event: workflow_dispatch

deploy:
  environments:
    - name: dev
      auto: true
      health_check: http://localhost:8080/actuator/health
    - name: prod
      auto: false
      strategy: canary
```

### 自动检测

`opspulse project init` 自动检测：
- CI 后端（GHA / Jenkins / Harness / GitLab CI）
- 项目模块（Maven 多模块 / npm monorepo）
- 编程语言（Java / Python / Go / Rust）
- 配置文件（Dockerfile / application.yml）
- Maven 依赖

---

## 与 MCP 的关系

| 层面 | 工具 | 用途 |
|------|------|------|
| **CLI 层** | `opspulse` 命令 | 人类直接操作，零门槛 |
| **MCP 层** | 11 个 MCP Tools | AI Agent 自动调用，无缝衔接 |

**CLI 和 MCP 共享底层能力，互不冲突。**

CLI 是基础，MCP 是扩展。

---

## 文件结构

```
ops-pulse/
├── mcp-server/
│   └── src/opspulse_mcp/
│       ├── cli.py                    # CLI 入口（重写）
│       ├── project/
│       │   ├── scanner.py            # 项目扫描器
│       │   └── generator.py          # 配置生成器
│       ├── parsers/
│       │   ├── frontmatter.py        # YAML frontmatter 解析
│       │   ├── validation.py         # Schema 校验
│       │   └── label_mapper.py       # GitHub Labels 映射
│       ├── workflow.py               # 状态机
│       ├── github/
│       │   └── client.py             # GitHub API 客户端
│       ├── tools/                    # 11 个 MCP Tools（保留）
│       └── server.py                 # MCP Server（保留）
├── schemas/
│   └── issue-spec.v1.json            # Spec Schema
├── doc/                              # 文档
└── README.md
```

---

## 使用示例

### 场景 1：快速创建一个 Issue 并处理

```bash
# 创建 Issue
opspulse new --owner myorg --repo myapp --title "Add refund API" \
  --service order-service

# 输出: Issue #45 created

# 处理 Issue
opspulse handle --owner myorg --repo myapp --issue 45

# 输出:
#   🔍 拉取 Issue #45...
#   ✅ Spec 解析成功
#   ✅ PR 已创建: https://github.com/.../pull/46
#   ✅ CI 已触发
#   ✅ 状态已回写
```

### 场景 2：分步执行，人工确认

```bash
# 只解析 + 创建 PR
opspulse handle --owner myorg --repo myapp --issue 45 --step pr

# 人工审查 PR 后，触发 CI
opspulse handle --owner myorg --repo myapp --issue 45 --step ci

# 人工确认部署
opspulse handle --owner myorg --repo myapp --issue 45 --step status
```

### 场景 3：查看交付日志

```bash
opspulse log --owner myorg --repo myapp --issue 45

# 输出:
#   📜 Issue #45 交付日志
#   ==========================================
#   Issue: Add refund API
#   状态: open
#   创建: 2026-07-07T10:00:00Z
#   更新: 2026-07-07T11:30:00Z
#
#   [2026-07-07T10:05:00Z] 🤖 github-actions:
#     ## OpsPulse Spec
#     ...
#   [2026-07-07T11:30:00Z] 🤖 github-actions:
#     ## OpsPulse 状态更新
#     状态: deployed
#     ...
```

---

## 设计决策

### 为什么是 CLI 而不是 Web UI？

1. **AI 友好**：CLI 命令可以被 AI Agent 直接调用
2. **脚本友好**：可以写成 shell 脚本自动化
3. **零依赖**：只需要 GitHub Token，不需要额外服务
4. **可组合**：每个命令独立，组合起来就是完整流水线

### 为什么配置在项目根目录？

1. **一次配置，处处可用**：CI、MCP、CLI 都读取同一个配置
2. **版本控制**：配置随代码一起提交，不会丢失
3. **可移植**：克隆项目即可使用，不需要额外安装

### 为什么保留 MCP 层？

1. **CLI 给人用，MCP 给 AI 用**：各司其职
2. **能力共享**：底层解析、校验、状态机都是同一套代码
3. **渐进采用**：不需要 MCP 也能用 CLI，有了 MCP 更强大

---

## 后续演进

### Phase 1：CLI 核心（当前）
- [x] `new` — 创建 Issue
- [x] `handle` — 处理 Issue
- [x] `review` — 评审 Spec
- [x] `log` — 查看日志
- [x] `project init` — 项目扫描
- [x] `project show` — 显示配置

### Phase 2：增强
- [ ] `handle --step ci` — CI 等待 + 健康检查
- [ ] `handle --step deploy` — 灰度部署 + 自动回滚
- [ ] `project edit` — 交互式编辑配置
- [ ] `project sync` — 同步到多个项目

### Phase 3：自动化
- [ ] `cron` — 定时检查未处理的 Issue
- [ ] `alert` — 交付失败通知
- [ ] `report` — 交付效率报告
