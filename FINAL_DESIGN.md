# OpsPulse 最终设计总结

> 纯 CLI 胶水层 + 项目级自定义配置工作流

---

## 一、核心设计理念

### 借鉴 oh-my-config

```
oh-my-config:  项目级配置 → AI 写代码时自动带连接串
OpsPulse:      项目级配置 → AI 交付时自动走正确流程
```

**共同点：配置在项目根目录，一次扫描，处处可用。**

### 配置文件

```
项目根目录:
├── .omc.json          # 连接信息（oh-my-config）
├── .opspulse.yaml     # 交付流程（OpsPulse）← 新增
├── AGENTS.md          # AI 行为规范
├── .github/workflows/ # CI 配置
└── src/               # 业务代码
```

---

## 二、CLI 命令

### 6 个命令

| 命令 | 用途 | 示例 |
|------|------|------|
| `opspulse new` | 交互式创建 Issue | `opspulse new --owner myorg --repo myapp --title "Add refund API"` |
| `opspulse project init` | 扫描项目，生成 `.opspulse.yaml` | `opspulse project init /path/to/project` |
| `opspulse project show` | 显示项目配置 | `opspulse project show` |
| `opspulse handle` | 处理 Issue（核心） | `opspulse handle --owner myorg --repo myapp --issue 45` |
| `opspulse review` | 评审 Issue Spec | `opspulse review --owner myorg --repo myapp --issue 45` |
| `opspulse log` | 查看交付日志 | `opspulse log --owner myorg --repo myapp --issue 45` |

### handle 分步执行

```bash
# 分步执行（安全）
opspulse handle --issue 45 --stage parse    # 解析 Spec
opspulse handle --issue 45 --stage pr        # 创建 PR（人工审查）
opspulse handle --issue 45 --stage ci        # 触发 CI
opspulse handle --issue 45 --stage status    # 回写状态

# 信任模式（全自动）
opspulse handle --issue 45 --stage all --auto
```

---

## 三、项目扫描

```bash
opspulse project init /path/to/project
```

自动检测：
- CI 后端（GHA / Jenkins / Harness / GitLab CI）
- 项目模块（Maven 多模块 / npm monorepo）
- 编程语言（Java / Python / Go / Rust）
- 配置文件（Dockerfile / application.yml / nginx.conf）
- Maven 依赖

生成 `.opspulse.yaml`：
```yaml
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

---

## 四、与 MCP 的关系

| 层面 | 工具 | 用途 |
|------|------|------|
| **CLI 层** | `opspulse` 命令 | 人类直接操作，零门槛 |
| **MCP 层** | 11 个 MCP Tools | AI Agent 自动调用，无缝衔接 |

**CLI 和 MCP 共享底层能力，互不冲突。**

---

## 五、文件清单

| 文件 | 说明 |
|------|------|
| `mcp-server/src/opspulse_mcp/cli.py` | CLI 入口（重写） |
| `mcp-server/src/opspulse_mcp/project/scanner.py` | 项目扫描器 |
| `mcp-server/src/opspulse_mcp/project/__init__.py` | 项目模块初始化 |
| `mcp-server/src/opspulse_mcp/github/client.py` | GitHub API 客户端 |
| `mcp-server/src/opspulse_mcp/workflow.py` | 状态机 |
| `mcp-server/src/opspulse_mcp/parsers/` | Spec 解析器 |
| `mcp-server/src/opspulse_mcp/tools/` | 11 个 MCP Tools |
| `CONFIG_WORKFLOW_DESIGN.md` | 设计文档 |
| `CLI_USAGE.md` | 使用指南 |
| `OLD_VS_NEW.md` | 新旧设计对比 |
| `REDESIGN.md` | 重构设计 |
| `FINAL_DESIGN.md` | 本文档 |
