# OpsPulse CLI 使用指南

> **纯命令行胶水层，零依赖 MCP/AI Agent**
> 一条命令完成 Issue → PR → CI → 部署 → 回写全流程

---

## 快速开始

```bash
# 1. 配置 GitHub Token
export GITHUB_PAT=your_token_here

# 2. 创建 Issue
opspulse new --owner myorg --repo myapp --title "Add refund API" --service order-service

# 3. 处理 Issue（自动走完全流程）
opspulse handle --owner myorg --repo myapp --issue 45 --stage all

# 4. 评审 Issue
opspulse review --owner myorg --repo myapp --issue 45

# 5. 查看交付日志
opspulse log --owner myorg --repo myapp --issue 45
```

---

## 命令详解

### `opspulse new` — 创建 Issue

交互式创建 Issue，引导填写服务名、验收标准、影响路径。

```bash
opspulse new \
  --owner myorg \
  --repo myapp \
  --title "Add user login" \
  --type feature \
  --service auth-service \
  --scope api \
  --priority P0 \
  --paths "auth-service/src/login.java,auth-service/src/token.py"
```

**可选参数：**
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--owner` | GitHub 组织/用户名 | 必填 |
| `--repo` | 仓库名 | 必填 |
| `--title` | Issue 标题 | 交互式提示 |
| `--type` | 类型 | `feature` |
| `--service` | 服务名 | 交互式提示 |
| `--scope` | 范围 | `api` |
| `--priority` | 优先级 | `P1` |
| `--paths` | 影响路径 | 交互式提示 |

### `opspulse handle` — 处理 Issue（核心命令）

从 Issue 解析 → 设计方案 → 任务拆分 → 创建 PR → 触发 CI → 回写状态。

```bash
# 完整流水线
opspulse handle --owner myorg --repo myapp --issue 45 --stage all

# 只创建 PR
opspulse handle --owner myorg --repo myapp --issue 45 --stage pr

# 只回写状态
opspulse handle --owner myorg --repo myapp --issue 45 --stage status
```

**可选参数：**
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--stage` | 执行阶段 | `all` |
| `--mode` | CI 模式 | `github-actions` |
| `--workflow` | GHA workflow 文件名 | `cicd.yml` |
| `--force` | 跳过 Spec 验证 | `false` |
| `--wait` | 等待 CI 完成 | `false` |

### `opspulse review` — 评审 Issue

检查 Issue 的 Spec 完整性，输出评审报告。

```bash
opspulse review --owner myorg --repo myapp --issue 45
```

### `opspulse log` — 查看交付日志

查看 Issue 下的所有 OpsPulse 相关 Comment 和状态变更。

```bash
opspulse log --owner myorg --repo myapp --issue 45
```

---

## 工作流程

```
opspulse new          → 创建 Issue + 写入 Spec Comment
       ↓
opspulse handle       → 解析 Spec → 创建 PR → 触发 CI → 回写状态
       ↓
opspulse review       → 检查 Spec 完整性
       ↓
opspulse log          → 查看所有交付记录
```

---

## 与 MCP Server 的关系

| 层面 | 工具 | 用途 |
|------|------|------|
| **CLI 层** | `opspulse` 命令 | 人类直接操作，零门槛 |
| **MCP 层** | 11 个 MCP Tools | AI Agent 自动调用，无缝衔接 |

CLI 和 MCP 共享底层能力（parse_issue, trigger_pipeline, update_issue_status 等），只是调用方式不同：

- **人用 CLI**：`opspulse handle --issue 45`
- **AI 用 MCP**：`ops_create_pr(issue_number=45, ...)`

---

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `GITHUB_PAT` | GitHub Personal Access Token | ✅ |
| `GITHUB_TOKEN` | 备选 Token | ❌ |

Token 需要 `repo` scope。

---

## 示例场景

### 场景 1：创建一个新功能

```bash
# 1. 创建 Issue
opspulse new --owner myorg --repo myapp --title "Add payment webhook" --service payment-service --priority P1

# 2. 处理（自动创建 PR、触发 CI）
opspulse handle --owner myorg --repo myapp --issue 42 --stage all --wait

# 3. 查看结果
opspulse log --owner myorg --repo myapp --issue 42
```

### 场景 2：修复一个 Bug

```bash
# 1. 创建 Bug Issue
opspulse new --owner myorg --repo myapp --title "Fix null pointer in order service" --type bugfix --service order-service --priority P0

# 2. 评审
opspulse review --owner myorg --repo myapp --issue 43

# 3. 处理
opspulse handle --owner myorg --repo myapp --issue 43 --stage all
```

---

## 故障排查

### 问题：`GITHUB_PAT` 未配置

```bash
export GITHUB_PAT=ghp_your_token_here
```

### 问题：Spec 验证失败

```bash
opspulse handle --issue 45 --force  # 跳过验证
```

### 问题：CI 触发失败

检查 GHA workflow 文件是否存在：
```bash
# 确认 cicd.yml 在 .github/workflows/ 下
curl -s https://api.github.com/repos/myorg/myapp/contents/.github/workflows/cicd.yml
```

---

## 下一步

- [ ] 接入真实 Java 项目测试
- [ ] 补充 Docker 部署能力
- [ ] 添加更多 CI 后端适配
