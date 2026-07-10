# OpsPulse 工作流模板系统设计

> 工作流即配置，模板即流程，CLI 按模板执行

---

## 一、核心概念

### 工作流 = 可配置的节点序列

```
需求: 我想用 TDD 模式开发
需求: 另一个需求我想用正常模式开发
需求: 我想可视化地看到流程节点
需求: 我想选模板，配好了 CLI 自动按模式执行
```

**答案：工作流模板系统。**

---

## 二、模板定义

### 内置模板

```yaml
# 模板 1: TDD 模式
templates:
  tdd:
    name: "TDD 测试驱动开发"
    description: "红→绿→重构循环，每个 AC 先写测试再写实现"
    icon: 🧪
    stages:
      - id: parse
        name: "解析 Spec"
        auto: true
        command: "parse_issue"
        timeout: 300
        
      - id: design
        name: "技术方案设计"
        auto: false
        command: "ops_design"
        timeout: 3600
        requires_approval: true
        
      - id: test_write
        name: "编写测试用例"
        auto: true
        command: "write_tests"
        timeout: 1800
        description: "先写失败的测试（Red）"
        
      - id: test_fail
        name: "验证测试失败"
        auto: true
        command: "run_tests --expect-failure"
        timeout: 600
        description: "确认测试确实失败了（红）"
        on_failure: abort
        error_message: "测试通过了？说明测试有问题，请检查"
        
      - id: code_implement
        name: "编写实现代码"
        auto: true
        command: "implement_code"
        timeout: 7200
        description: "写最少代码让测试通过（绿）"
        
      - id: test_pass
        name: "验证测试通过"
        auto: true
        command: "run_tests --expect-pass"
        timeout: 600
        description: "确认测试通过了（绿）"
        on_failure: rollback
        error_message: "测试没通过，代码有问题，请检查"
        
      - id: refactor
        name: "重构"
        auto: false
        command: "refactor_code"
        timeout: 3600
        description: "清理代码，保持测试通过"
        requires_approval: true
        
      - id: pr_create
        name: "创建 PR"
        auto: true
        command: "ops_create_pr"
        timeout: 300
        
      - id: ci_trigger
        name: "触发 CI"
        auto: true
        command: "trigger_ci"
        timeout: 1800
        wait: true
        
      - id: smoke_test
        name: "冒烟测试"
        auto: true
        command: "ops_smoke_test"
        timeout: 900
        
      - id: deploy
        name: "部署"
        auto: false
        command: "ops_deploy"
        timeout: 1800
        requires_approval: true
        
      - id: status_update
        name: "回写状态"
        auto: true
        command: "update_issue_status"
        timeout: 60

# 模板 2: 正常开发模式
  normal:
    name: "标准开发流程"
    description: "设计→编码→PR→CI→部署"
    icon: ⚡
    stages:
      - id: parse
        name: "解析 Spec"
        auto: true
        command: "parse_issue"
        
      - id: design
        name: "技术方案设计"
        auto: false
        command: "ops_design"
        requires_approval: true
        
      - id: code_implement
        name: "编写代码"
        auto: true
        command: "implement_code"
        
      - id: pr_create
        name: "创建 PR"
        auto: true
        command: "ops_create_pr"
        
      - id: ci_trigger
        name: "触发 CI"
        auto: true
        command: "trigger_ci"
        wait: true
        
      - id: deploy
        name: "部署"
        auto: false
        command: "ops_deploy"
        requires_approval: true
        
      - id: status_update
        name: "回写状态"
        auto: true
        command: "update_issue_status"

# 模板 3: 紧急修复
  hotfix:
    name: "紧急修复"
    description: "跳过设计，直接修复+验证"
    icon: 🔥
    stages:
      - id: parse
        name: "解析 Spec"
        auto: true
        command: "parse_issue"
        
      - id: code_implement
        name: "编写修复代码"
        auto: true
        command: "implement_code"
        
      - id: test_pass
        name: "验证测试"
        auto: true
        command: "run_tests"
        
      - id: pr_create
        name: "创建 PR"
        auto: true
        command: "ops_create_pr"
        
      - id: ci_trigger
        name: "触发 CI"
        auto: true
        command: "trigger_ci"
        wait: true
        
      - id: deploy
        name: "紧急部署"
        auto: false
        command: "ops_deploy --hotfix"
        requires_approval: true

# 模板 4: 大型功能
  feature:
    name: "大型功能开发"
    description: "拆分→并行→集成→全面测试"
    icon: 🏗️
    stages:
      - id: parse
        name: "解析 Spec"
        auto: true
        command: "parse_issue"
        
      - id: design
        name: "技术方案设计"
        auto: false
        command: "ops_design"
        requires_approval: true
        
      - id: breakdown
        name: "任务拆分"
        auto: true
        command: "ops_breakdown"
        
      - id: coding_parallel
        name: "并行编码"
        auto: true
        command: "ops_code_agent --parallel"
        sub_stages:
          - name: "实现子任务 1"
            command: "implement_subtask --index 1"
          - name: "实现子任务 2"
            command: "implement_subtask --index 2"
          - name: "实现子任务 3"
            command: "implement_subtask --index 3"
            
      - id: integration
        name: "集成测试"
        auto: true
        command: "run_integration_tests"
        
      - id: pr_create
        name: "创建 PR"
        auto: true
        command: "ops_create_pr"
        
      - id: ci_trigger
        name: "触发 CI"
        auto: true
        command: "trigger_ci"
        wait: true
        
      - id: deploy
        name: "部署"
        auto: false
        command: "ops_deploy"
        requires_approval: true
```

---

## 三、项目级工作流配置

### `.opspulse.yaml` — 项目工作流配置

```yaml
# 项目标识
project:
  name: order-service
  modules: [gateway, web, bpm, order-service]

# 默认模板
defaults:
  template: normal          # 默认使用 normal 模板
  ci_backend: github-actions
  
# 自定义模板（项目级覆盖）
custom_templates:
  tdd-with-reviews:
    extends: tdd            # 继承内置模板
    name: "TDD + 代码审查"
    description: "TDD 模式，每个阶段都需要人工审查"
    stages:
      - id: design
        requires_approval: true
      - id: refactor
        requires_approval: true
      - id: code_implement
        requires_approval: true

# 项目级 CI 配置
ci:
  backend: github-actions
  github-actions:
    workflow_file: .github/workflows/cicd.yml

# 项目级部署配置
deploy:
  environments:
    - name: dev
      auto: true
    - name: prod
      auto: false
      strategy: canary
```

---

## 四、可视化流程节点

### 终端可视化（CLI 内）

```bash
opspulse handle --issue 45 --template tdd

# 输出:
#
# ╔══════════════════════════════════════════════════════════╗
# ║                    工作流执行进度                         ║
# ╚══════════════════════════════════════════════════════════╝
#
# 🧪 TDD 测试驱动开发
#
# [████████████████████████████████████████████████████] 100%
#
#  1. ✅ 解析 Spec          (自动完成)
#  2. ✅ 技术方案设计        (人工审查通过)
#  3. ✅ 编写测试用例       (Red - 测试失败 ✓)
#  4. ✅ 验证测试失败       (确认 Red)
#  5. ✅ 编写实现代码       (Green - 测试通过 ✓)
#  6. ✅ 验证测试通过       (确认 Green)
#  7. ⏸️  重构              (等待人工审查...)
#  8. ⬜ 创建 PR
#  9. ⬜ 触发 CI
# 10. ⬜ 冒烟测试
# 11. ⬜ 部署
# 12. ⬜ 回写状态
#
# 当前节点: 重构 (requires_approval: true)
# 按 Enter 继续审查...
```

### 节点详情

每个节点包含：
- **ID**：唯一标识
- **名称**：人类可读
- **图标**：视觉区分
- **状态**：⬜未开始 / ⏳进行中 / ✅完成 / ❌失败 / ⏸️等待
- **自动/手动**：是否自动执行
- **超时**：最大等待时间
- **失败策略**：abort（中止）/ rollback（回滚）/ continue（继续）
- **审批**：是否需要人工批准

---

## 五、CLI 命令

### 模板管理

```bash
# 列出所有模板
opspulse templates list

# 查看模板详情
opspulse templates show tdd

# 创建自定义模板
opspulse templates create my-template --from tdd

# 编辑模板
opspulse templates edit my-template

# 删除模板
opspulse templates delete my-template

# 导出模板
opspulse templates export my-template > my-template.yaml

# 导入模板
opspulse templates import my-template.yaml
```

### 工作流执行

```bash
# 使用默认模板
opspulse handle --issue 45

# 指定模板
opspulse handle --issue 45 --template tdd

# 指定模板 + 分步执行
opspulse handle --issue 45 --template tdd --step test_write

# 可视化进度
opspulse handle --issue 45 --template tdd --visual

# 信任模式（跳过人工确认）
opspulse handle --issue 45 --template tdd --auto
```

### 项目配置

```bash
# 初始化项目（生成 .opspulse.yaml）
opspulse project init /path/to/project

# 查看当前配置
opspulse project show

# 设置默认模板
opspulse project set-default-template tdd

# 切换默认模板
opspulse project set-default-template normal
```

---

## 六、节点类型

### 预定义节点

| 节点类型 | 命令 | 说明 |
|---------|------|------|
| `parse_issue` | 解析 Issue | 从 frontmatter 提取 Spec |
| `ops_design` | 设计方案 | 生成技术设计方案 |
| `ops_breakdown` | 任务拆分 | 拆分为子任务 |
| `write_tests` | 编写测试 | 生成测试用例 |
| `run_tests` | 运行测试 | 执行测试套件 |
| `implement_code` | 编写代码 | 实现功能 |
| `refactor_code` | 重构 | 清理代码 |
| `ops_create_pr` | 创建 PR | 自动创建分支+PR |
| `trigger_ci` | 触发 CI | 调用 CI 后端 |
| `ops_smoke_test` | 冒烟测试 | 健康检查 + AC 验证 |
| `ops_deploy` | 部署 | 灰度/全量部署 |
| `update_issue_status` | 回写状态 | 更新 Issue Comment |

### 自定义节点

用户可以添加自定义节点：

```yaml
custom_templates:
  my-custom:
    stages:
      - id: my_step
        name: "我的自定义步骤"
        command: "my_custom_script.sh"
        auto: true
        timeout: 300
```

---

## 七、实现方案

### Phase 1：模板系统

```
mcp-server/src/opspulse_mcp/
├── templates/
│   ├── __init__.py           # 模板管理器
│   ├── builtin.py            # 内置模板
│   ├── loader.py             # 模板加载（项目级 + 内置）
│   └── validator.py          # 模板校验
├── workflow/
│   ├── engine.py             # 工作流引擎（执行模板）
│   ├── node.py               # 节点抽象
│   ├── runner.py             # 节点执行器
│   └── visual.py             # 终端可视化
└── ...
```

### Phase 2：CLI 集成

```python
# opspulse handle --template tdd
# 1. 加载 .opspulse.yaml
# 2. 解析 template: tdd
# 3. 合并内置模板 + 项目级覆盖
# 4. 执行工作流引擎
# 5. 可视化进度
```

### Phase 3：节点执行

```python
# 每个节点是一个可执行单元
class WorkflowNode:
    def __init__(self, spec: dict):
        self.id = spec['id']
        self.name = spec['name']
        self.command = spec['command']
        self.auto = spec.get('auto', False)
        self.timeout = spec.get('timeout', 300)
        self.on_failure = spec.get('on_failure', 'continue')
        self.requires_approval = spec.get('requires_approval', False)
    
    def execute(self) -> NodeResult:
        # 1. 检查是否需要人工审批
        if self.requires_approval and not self.auto:
            self.wait_for_approval()
        
        # 2. 执行命令
        result = subprocess.run(self.command, timeout=self.timeout)
        
        # 3. 根据结果处理
        if result.returncode != 0:
            if self.on_failure == 'abort':
                raise WorkflowAbortError(...)
            elif self.on_failure == 'rollback':
                self.rollback()
        
        return NodeResult(self.id, result)
```

---

## 八、一句话总结

> **工作流模板 = 可配置的节点序列。CLI 按模板执行，节点可视化展示，模板可继承、可覆盖、可扩展。**
