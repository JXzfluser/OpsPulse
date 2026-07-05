# OpsPulse 完整交付闭环架构设计

> **目标**：从 Issue 录入到生产部署的全自动闭环
> **核心思路**：一个 Issue 贯穿整个软件工程生命周期，AI Agent 在每个阶段自动推进

---

## 一、当前状态 vs 目标

### 当前（v0.3.0）
```
Issue → parse_issue → trigger_pipeline → update_issue_status
  ↓                    ↓                       ↓
  解析 Spec           触发 GHA               回写 Comment
```
**覆盖**：解析 + 触发 CI + 回写（约 30%）

### 目标（v1.0.0 完整闭环）
```
需求录入 → 需求评审 → 设计方案 → 任务拆分 → 编码 → PR → 验证 → 部署 → 回写
   ↓          ↓          ↓          ↓         ↓     ↓     ↓      ↓      ↓
 parse     review     design    breakdown  code   pr   verify deploy  status
```
**覆盖**：10 个阶段，全部自动化

---

## 二、完整闭环架构

### Phase 1：需求阶段（Issue 录入 → 需求评审）

#### 1.1 需求录入（已有）
- 产品/TL 在 GitHub 创建 Issue
- Issue 模板：`auto-dev-feature.yml` / `auto-dev-bugfix.yml`
- frontmatter 包含：service, build, deploy, acceptance

#### 1.2 需求评审（新增）
- **触发**：Issue 创建后，ops-pulse-review 机器人自动评论
- **评审 Checklist**：
  - [ ] 需求描述是否清晰（有无背景、目标、验收标准）
  - [ ] affected_paths 是否合理（会不会影响不相关的服务）
  - [ ] acceptance criteria 是否可测试
  - [ ] 是否有依赖的其他服务/接口变更
  - [ ] 优先级和排期是否合理
- **评审结果**：
  - ✅ 通过 → 状态变更为 `review-passed`，自动进入设计方案
  - ❌ 驳回 → 自动 Comment 说明原因，Issue 保持 `review-rejected`
  - ⚠️ 需修改 → 自动 Comment 列出需修改项，开发者补充后重新评审

**实现**：新增 `ops_review` MCP Tool
```python
def ops_review(issue_number: int, reviewer: str, approved: bool, comments: str) -> dict:
    """需求评审：自动检查 checklist 并给出评审意见"""
```

### Phase 2：设计阶段（设计方案 → 任务拆分）

#### 2.1 设计方案（新增）
- **触发**：需求评审通过后
- **AI Agent 自动生成设计方案**：
  - 基于 Issue Spec 的 acceptance criteria
  - 参考 affected_paths 的代码结构
  - 输出：数据库变更、API 变更、配置变更、依赖变更
- **设计评审**：TL/架构师审批设计文档

**实现**：新增 `ops_design` MCP Tool
```python
def ops_design(issue_number: int) -> dict:
    """根据 Issue Spec 自动生成技术方案文档"""
```

#### 2.2 任务拆分（新增）
- **触发**：设计方案批准后
- **AI Agent 拆分为可执行任务**：
  - 每个任务对应一个 sub-issue 或 checklist item
  - 任务之间有依赖关系（DAG）
  - 每个任务有明确的验收标准

**实现**：新增 `ops_breakdown` MCP Tool
```python
def ops_breakdown(issue_number: int) -> dict:
    """将 Issue 拆分为可执行的任务列表"""
```

### Phase 3：开发阶段（编码 → PR）

#### 3.1 编码（已有 + 增强）
- **触发**：任务拆分完成后
- **AI Agent 基于 Issue Spec 编码**：
  - 使用 `issue-to-code.md` prompt
  - 只修改 affected_paths 范围内的文件
  - 保持 JDK 8 兼容性
  - 自动生成单元测试

#### 3.2 PR 创建（已有 + 增强）
- **触发**：编码完成后
- **AI Agent 自动创建 PR**：
  - PR 标题：`[Issue #N] {service}: {description}`
  - PR 描述：链接 Issue、列出 AC 完成情况
  - 自动关联 Issue

**实现**：新增 `ops_create_pr` MCP Tool
```python
def ops_create_pr(issue_number: int, branch: str, title: str, body: str) -> dict:
    """自动创建 PR 并关联 Issue"""
```

### Phase 4：验证阶段（PR 验证 → 冒烟测试）

#### 4.1 PR 验证（已有）
- **触发**：PR 创建后
- **自动触发 CI pipeline**：
  - 编译验证
  - 单元测试
  - 代码风格检查
  - 依赖安全扫描

#### 4.2 冒烟测试（新增）
- **触发**：PR 验证通过后
- **自动部署到测试环境**：
  - 部署到 staging 环境
  - 运行 acceptance criteria 对应的冒烟测试
  - 输出测试结果

**实现**：增强 `trigger_pipeline` 支持 staging 部署
```python
def ops_smoke_test(issue_number: int, pipeline_id: str) -> dict:
    """冒烟测试：部署到 staging 并验证 acceptance criteria"""
```

### Phase 5：部署阶段（发布到生产）

#### 5.1 灰度发布（新增）
- **触发**：冒烟测试通过后
- **自动灰度部署**：
  - 先部署到 10% 流量
  - 监控错误率和性能指标
  - 自动回滚 if 异常

#### 5.2 全量发布（已有）
- **触发**：灰度通过后
- **deploy-dev → deploy-staging → deploy-prod**

**实现**：新增 `ops_deploy` MCP Tool
```python
def ops_deploy(issue_number: int, environment: str, percentage: int = 100) -> dict:
    """灰度/全量部署，支持自动回滚"""
```

### Phase 6：回写阶段（闭环）

#### 6.1 状态回写（已有）
- **触发**：部署完成后
- **自动更新 Issue 状态**：
  - 状态变更为 `deployed`
  - 发布 Comment 包含：部署环境、版本号、验证结果
  - 关闭 Issue

---

## 三、状态机

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                                                         │
                    ▼                                                         │
  [created] → [review-pending] → [review-passed] → [design-pending] → [design-approved]
      ↑              │                    │                    │                    │
      │              ▼                    ▼                    ▼                    ▼
      │        [review-rejected]    [design-rejected]    [breakdown-done]   [coding-done]
      │              │                    │                    │                    │
      │              │                    │                    ▼                    ▼
      │              │                    │            [pr-created] → [pr-verifying]
      │              │                    │                    │                    │
      │              │                    │                    ▼                    │
      │              │                    │            [pr-verified] → [smoke-testing]
      │              │                    │                    │                    │
      │              │                    │                    ▼                    │
      │              │                    │            [smoke-passed] → [deploying]
      │              │                    │                    │                    │
      │              │                    │                    ▼                    │
      │              │                    │            [deployed] → [closed] ◄─────┘
      │              │                    │                    │
      │              │                    │                    ▼
      └──────────────┴────────────────────┴──────────────── [rollback] → [deploying]
```

---

## 四、新增 MCP Tools 清单

| Tool | 职责 | 输入 | 输出 |
|------|------|------|------|
| `ops_review` | 需求评审 | issue_number, reviewer, approved, comments | 评审结果 + Comment |
| `ops_design` | 生成设计方案 | issue_number | 设计文档（Markdown） |
| `ops_breakdown` | 任务拆分 | issue_number, design_doc | 任务列表（JSON） |
| `ops_create_pr` | 创建 PR | issue_number, branch, title, body | PR URL + 关联 Issue |
| `ops_smoke_test` | 冒烟测试 | issue_number, pipeline_id | 测试结果 |
| `ops_deploy` | 灰度/全量部署 | issue_number, env, percentage | 部署状态 + 回滚策略 |

---

## 五、开发计划

### Sprint 1（本周）：需求评审 + 设计方案
- [ ] 实现 `ops_review` Tool
- [ ] 实现 `ops_design` Tool
- [ ] 更新 Issue 状态机
- [ ] 端到端测试

### Sprint 2（下周）：任务拆分 + PR 创建
- [ ] 实现 `ops_breakdown` Tool
- [ ] 实现 `ops_create_pr` Tool
- [ ] 增强 GitHub API client
- [ ] 端到端测试

### Sprint 3（下下周）：验证 + 部署
- [ ] 实现 `ops_smoke_test` Tool
- [ ] 实现 `ops_deploy` Tool
- [ ] 灰度发布逻辑
- [ ] 自动回滚

### Sprint 4（下下下周）：闭环 + 优化
- [ ] 完整状态机
- [ ] 错误处理 + 重试
- [ ] 监控 + 告警
- [ ] 文档完善

---

## 六、关键设计原则

1. **Issue 是唯一事实来源** — 所有阶段的状态都写在 Issue 上
2. **AI Agent 驱动** — 每个阶段由 AI 自动推进，人工只在关键节点审批
3. **可回滚** — 每个阶段都可以回退到上一阶段
4. **可追溯** — 每个决策都有 Comment 记录
5. **渐进式** — 可以先用 parse_issue + trigger_pipeline，逐步增加新 Tool
