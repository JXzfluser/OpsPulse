# OpsPulse

> **Issue-to-Deploy 纯 CLI 胶水层** — 零 MCP 依赖，零外部服务，GitHub Issue 直达生产部署。

## 一句话定位

OpsPulse 把 GitHub Issue 变成可执行的交付流水线：**Issue → Spec → PR → CI → Deploy**，全程 CLI 驱动。

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/JXzfluser/OpsPulse.git
cd OpsPulse/mcp-server
source .venv/bin/activate

# 2. 设置 GitHub Token
export GITHUB_PAT="ghp_xxxxxxxxxxxx"

# 3. 初始化项目配置（自动检测 CI 后端、语言、模块）
opspulse project init /path/to/your/project

# 4. 查看所有可用模板
opspulse templates list

# 5. 查看模板详情
opspulse templates show tdd

# 6. 交互式创建 Issue
opspulse new --owner myorg --repo myapp --title "Add refund API" \
  --type feature --service payment --priority P1

# 7. 处理 Issue（全自动流水线）
opspulse handle --owner myorg --repo myapp --issue 45 --template tdd

# 8. 查看交付日志
opspulse log --owner myorg --repo myapp --issue 45
```

## 命令参考

### `opspulse new` — 创建 Issue

```bash
# 交互式（推荐）
opspulse new --owner myorg --repo myapp

# 指定参数
opspulse new --owner myorg --repo myapp \
  --title "Implement user authentication" \
  --type feature \
  --service auth-service \
  --priority P0 \
  --scope api \
  --description "OAuth2 + JWT 认证"
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--owner` | ✅ | GitHub 组织/用户名 |
| `--repo` | ✅ | 仓库名 |
| `--title` | | Issue 标题（交互式会提示） |
| `--type` | | `feature` / `bugfix` / `chore` / `infra` |
| `--service` | | 服务名 |
| `--scope` | | `api` / `config` / `deploy` / `infra` / `docs` |
| `--priority` | | `P0` / `P1` / `P2` / `P3` |
| `--paths` | | 影响路径（逗号分隔） |
| `--description` | | 需求描述 |

### `opspulse handle` — 处理 Issue（核心命令）

```bash
# 完整流水线（默认）
opspulse handle --owner myorg --repo myapp --issue 45 --template tdd

# 只创建 PR
opspulse handle --owner myorg --repo myapp --issue 45 --stage pr

# 本地模式（跳过 CI）
opspulse handle --owner myorg --repo myapp --issue 45 --mode local

# 跳过验证
opspulse handle --owner myorg --repo myapp --issue 45 --force

# 等待 CI 完成
opspulse handle --owner myorg --repo myapp --issue 45 --wait
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--owner` | ✅ | GitHub owner |
| `--repo` | ✅ | GitHub repo |
| `--issue-number` | ✅ | Issue 编号 |
| `--stage` | | `all` / `pr` / `ci` / `status` |
| `--template` | | `tdd` / `normal` / `hotfix` / `feature` |
| `--mode` | | `github-actions` / `local` / `harness` |
| `--force` | | 跳过 Spec 验证 |
| `--wait` | | 等待 CI 完成 |

### `opspulse templates` — 模板管理

```bash
# 列出所有模板
opspulse templates list

# 查看 TDD 模板详情
opspulse templates show tdd
```

### `opspulse review` — 评审 Issue

```bash
opspulse review --owner myorg --repo myapp --issue 45
```

检查 Issue Spec 完整性，输出评审报告。

### `opspulse log` — 交付日志

```bash
opspulse log --owner myorg --repo myapp --issue 45
```

串联展示 Issue / PR / CI 全链路日志。

### `opspulse project` — 项目管理

```bash
# 扫描并生成配置
opspulse project init /path/to/project

# 查看当前配置
opspulse project show
```

## 工作流模板

| 模板 | 图标 | 适用场景 |
|------|------|----------|
| `tdd` | 🧪 | 测试驱动开发（红→绿→重构循环） |
| `normal` | ⚡ | 标准开发流程 |
| `hotfix` | 🔥 | 紧急修复（跳过评审，快速上线） |
| `feature` | 🏗️ | 大型功能开发（多阶段审批） |

### TDD 模板流程

```
[解析 Spec] → [方案设计] → [写测试(Red)] → [验证失败] → 
[写实现(Green)] → [验证通过] → [重构] → [创建 PR] → 
[触发 CI] → [冒烟测试] → [部署] → [回写状态]
```

## 项目配置

`opspulse project init` 自动生成 `.opspulse.yaml`：

```yaml
# OpsPulse 项目交付配置
project:
  name: my-app
  modules: ["payment-service", "order-service"]
  languages: ["java", "python"]

ci:
  backend: github-actions
  github-actions:
    workflow_file: .github/workflows/cicd.yml
    dispatch_event: workflow_dispatch

deploy:
  environments:
    - name: dev
      auto: true
    - name: staging
      auto: false
    - name: prod
      auto: false
      strategy: canary

workflow:
  stages:
    - name: parse
      auto: true
    - name: pr
      auto: false
    - name: ci
      auto: true
    - name: deploy
      auto: false
```

## 架构

```
opspulse/
├── cli.py                  # CLI 入口 + 命令处理
├── workflow.py             # 旧版 Issue 状态机
├── workflow_pkg/           # 新版工作流引擎
│   ├── engine.py           # 工作流引擎
│   ├── node.py             # 节点定义和执行
│   └── __init__.py
├── templates/              # 工作流模板
│   ├── builtin/            # 4 个内置模板 (YAML)
│   └── __init__.py
├── project/                # 项目扫描器
│   └── scanner.py
├── github/                 # GitHub API 客户端
│   └── client.py
└── parsers/                # 解析器
    ├── frontmatter.py      # Frontmatter 提取
    └── validation.py       # Spec 验证
```

## 提效数据

| 环节 | 手动 | OpsPulse | 提升 |
|------|------|----------|------|
| Issue 创建 | 5min | 2min | 60% |
| 分支管理 | 3min | 0min (自动) | 100% |
| PR 创建 | 5min | 0min (自动) | 100% |
| CI 触发 | 3min | 0min (自动) | 100% |
| 状态更新 | 2min | 0min (自动) | 100% |
| **总计/次** | **18min** | **2min** | **89%** |

## 环境要求

- Python 3.10+
- GitHub PAT (用于 API 访问)
- `httpx` (自动安装)

## 安装

```bash
cd mcp-server
source .venv/bin/activate
pip install -e .
```

## 测试

```bash
python -m pytest tests/ -v
```

## 许可证

MIT
