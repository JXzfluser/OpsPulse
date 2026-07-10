# OpsPulse 胶水层重构设计

> **核心矛盾**：直接 AI 对话门槛低但不可控，OpsPulse 可控但门槛高
> **设计目标**：默认零门槛，按需增强，能力不丢

---

## 一、设计原则

### 1. 胶水层应该在「用户意图」和「AI 执行」之间，而不是在「用户」和「AI」之间加一层操作

```
旧设计（门槛高）:
  用户 → 写 Issue frontmatter → MCP parse → AI 读 Spec → AI 编码

新设计（零门槛）:
  用户 → 说一句话 → AI 自动决定要不要结构化 → AI 编码
```

### 2. 结构化是「AI 的副产物」，不是「用户的输入」

用户不需要写 YAML frontmatter。AI 从对话中**自动提取**结构化信息，存入 Issue Comment 作为契约。

### 3. 能力分层，不是开关切换

| 层级 | 触发条件 | 用户感知 |
|------|----------|----------|
| L0 直接对话 | 默认 | 和 Cursor 对话一样 |
| L1 自动结构化 | AI 判断需求复杂 | Issue 下自动生成 Spec Comment |
| L2 流水线触发 | 用户说「跑 CI」或 AI 建议 | 自动 trigger_pipeline |
| L3 审计回写 | Issue 关闭时 | 自动 update_issue_status |

---

## 二、架构设计

### 核心变化：从「用户驱动」到「AI 驱动」

```
┌─────────────────────────────────────────────────────┐
│                    用户说一句话                       │
│              「帮我在 order-service 加个退款 API」      │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              AI Agent (Cursor / Claude Code)          │
│                                                     │
│  1. 理解意图                                         │
│  2. 自动提取结构化信息:                               │
│     - service: order-service                         │
│     - type: feature                                  │
│     - affected_paths: [order-service/src/...]        │
│     - acceptance: [退款成功后余额增加, 原订单状态更新]    │
│  3. 写入 Issue Comment (契约)                         │
│  4. 开始编码                                         │
│  5. 提交 PR                                          │
│  6. 触发 CI (如需)                                   │
│  7. 回写 Issue (如需)                                │
└─────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              OpsPulse MCP Server (后台)               │
│                                                     │
│  - parse_issue: 解析 Issue 下的 Spec Comment          │
│  - trigger_pipeline: 触发 CI                         │
│  - update_issue_status: 回写 Issue                   │
│  - ops_review/design/breakdown: 可选增强              │
│  - ops_code_agent: AI 编码桥接                        │
│  - ops_create_pr/smoke_test/deploy: 自动化流程        │
└─────────────────────────────────────────────────────┘
```

### 关键区别

**旧设计**：用户必须主动使用 OpsPulse 的每个工具
**新设计**：AI Agent 自动调用 OpsPulse 的工具，用户无感

---

## 三、具体实现方案

### 3.1 入口：一句话需求

```
用户: "帮我在 order-service 加个退款 API"
```

AI Agent 自动做以下事情：

1. **理解意图** → 这是一个 feature，影响 order-service
2. **查找仓库结构** → 找到 affected_paths
3. **生成 Spec** → 自动创建 frontmatter（不是用户写，是 AI 写）
4. **写入 Issue** → 作为 Comment 贴在 Issue 下
5. **开始编码** → 按 Spec 执行

### 3.2 Spec 的生成方式

**不再要求用户写 YAML frontmatter。**

AI 从对话中自动提取，生成 Spec：

```python
# AI 生成的 Spec Comment（贴在 Issue 下）
"""
## OpsPulse Spec

**service**: order-service
**type**: feature
**scope**: api
**affected_paths**:
  - order-service/src/main/java/com/example/order/
  - order-service/src/test/java/com/example/order/

**acceptance**:
  - AC-1: 调用退款 API，订单状态变为 refunded
  - AC-2: 用户余额增加退款金额
  - AC-3: 退款记录写入数据库

**generated_by**: AI Agent auto-extraction
"""
```

用户看不到这个过程，Issue 下自动多了一条 Comment。

### 3.3 何时启用结构化

| 场景 | AI 决策 | 行为 |
|------|---------|------|
| 简单需求（改个文案） | L0 | 直接编码，不调用 OpsPulse |
| 中等需求（加个 API） | L1 | 自动生成 Spec → 编码 → PR |
| 复杂需求（跨服务） | L2 | Spec + trigger_pipeline + 回写 |
| 用户说「跑 CI」 | L2 | 强制 trigger_pipeline |
| 用户说「部署到生产」 | L3 | ops_deploy |

### 3.4 OpsPulse 的角色转变

**从「用户必须学的工具」变为「AI 自动调用的基础设施」**

```
旧: 用户 → 学 MCP → 学 parse_issue → 学 trigger_pipeline
新: 用户 → 说话 → AI 自动调 parse_issue → AI 自动调 trigger_pipeline
```

用户不需要知道 OpsPulse 的存在。

---

## 四、MCP Server 保持不变

MCP 的 11 个工具全部保留，但**调用者变了**：

| 工具 | 旧调用者 | 新调用者 |
|------|----------|----------|
| parse_issue | 用户手动调用 | AI Agent 自动调用 |
| trigger_pipeline | 用户手动调用 | AI Agent 自动调用 |
| update_issue_status | 用户手动调用 | AI Agent 自动调用 |
| ops_create_pr | 用户手动调用 | AI Agent 自动调用 |
| ops_code_agent | 用户手动调用 | AI Agent 本身就是 |
| ops_review/design/breakdown | 用户手动调用 | AI Agent 自动调用 |
| ops_smoke_test/deploy | 用户手动调用 | AI Agent 自动调用 |

**代码不用改，只需要改 AI Agent 的行为。**

---

## 五、用户交互流程

### 场景 1：简单需求（零感知）

```
用户: "帮我把首页标题改成欢迎使用"
AI:   好的，已修改 index.html
用户: （无操作）
```

### 场景 2：中等需求（自动结构化）

```
用户: "帮我在 order-service 加个退款 API"
AI:   好的，我来处理。
      → [后台自动] 生成 Spec Comment 到 Issue #45
      → [后台自动] 创建分支 opspulse/45-refund-api
      → [后台自动] 编码 + 测试
      → [后台自动] 创建 PR
用户: PR 创建好了，要我审查吗？
AI:   是的，PR #46 已创建。
      → [后台自动] 触发 CI
      → [后台自动] CI 通过后部署到 dev
      → [后台自动] 回写 Issue
用户: （无操作，一切自动完成）
```

### 场景 3：用户主动控制

```
用户: "用结构化模式处理 Issue #45"
AI:   → 启用 parse_issue 校验 Spec
      → 生成设计方案
      → 任务拆分
      → 自动编码 + PR + CI + 部署
```

---

## 六、重构优先级

### Phase 1：AI 自动结构化（本周）
- [ ] 修改 AI Agent prompt，让它能从对话中自动提取 Spec
- [ ] Spec 写入 Issue Comment（不是 frontmatter）
- [ ] 保持 parse_issue 能读取 Comment 格式的 Spec

### Phase 2：AI 自动编排（下周）
- [ ] AI 在编码完成后自动调用 ops_create_pr
- [ ] AI 在 PR 创建后自动调用 trigger_pipeline
- [ ] AI 在 CI 通过后自动调用 ops_smoke_test

### Phase 3：按需增强（持续）
- [ ] 提供 `opspulse enhance` 命令，把自然语言需求转为结构化 Spec
- [ ] 提供 Issue 模板，用户可以选择性填写
- [ ] 保留所有现有 MCP 工具，作为 AI 的「工具箱」

---

## 七、核心价值主张

**旧主张**：「Issue 下单，流水线验货，Comment 结案」
**新主张**：「你说一句话，AI 搞定全流程」

**旧卖点**：结构化、可审计、合规
**新卖点**：零门槛、全自动、能力不丢

---

## 八、风险评估

| 风险 | 影响 | 缓解 |
|------|------|------|
| AI 自动提取 Spec 不准确 | 编码方向错误 | 生成后让 AI 自检 + 用户确认 |
| 过度自动化 | 用户失控感 | 保留手动触发入口 |
| 能力丢失 | 结构化模式不用了 | 所有能力保留，只是调用方式变了 |
| 学习曲线 | 团队不熟悉结构化 | 默认不强制，用时才有 |

---

## 九、一句话总结

> **OpsPulse 不是用户工具，是 AI 的基础设施。**
> 用户只负责说话，AI 负责调用 OpsPulse 的所有能力。
