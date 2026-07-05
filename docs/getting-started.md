# 快速上手

> **三句话交付**：读单 → 验货 → 结案。业务仓零安装。  
> 设计原则：[胶水层核心能力](../doc/胶水层核心能力.md)

---

## 1. 一次性配置（约 10 分钟）

```bash
cp .env.example .env          # 填入 GITHUB_PAT
cd mcp-server && uv sync --extra dev
docker pull ghcr.io/github/github-mcp-server
```

Cursor 使用本仓 `.cursor/mcp.json`，重载窗口后确认 **opspulse** / **github** 已连接。  
详见 [MCP 配置](./mcp-setup.md)。

---

## 2. 三个动词（日常只用这些）

| 动词 | 在 Cursor 里说 | MCP 工具 |
|------|----------------|----------|
| **读单** | 「处理 chuanplus-platform 的 Issue #12」 | `parse_issue` |
| **验货** | 「跑 pr-validation」 | `trigger_pipeline` |
| **结案** | 「部署完成，回写 Issue」 | `update_issue_status` |

**读单**返回 `ready: true` 后，Agent 只改 Issue 里 `affected_paths` 列出的文件。

---

## 3. 单命令（推荐）

```bash
chmod +x scripts/opspulse.sh

# 读单 + 可选验货（触发目标仓 GHA workflow_dispatch）
./scripts/opspulse.sh handle --owner JXzfluser --repo chuanplus-platform --issue N --verify
```

`opspulse.yaml` 的 `pipeline.github_actions.repositories` 映射目标仓 workflow（如 `cicd.yml`）。  
Issue frontmatter 可含 `repository` + `ci` 覆盖，见 `examples/issues/004-chuanplus-gateway.md`。

---

## 4. 业务仓怎么接（零侵入）

OpsPulse **不复制进**你的微服务仓库。

```
你的业务仓（如 chuanplus-platform）
  └── 只有业务代码 + 你原有的 CI

OpsPulse 仓（或全局 MCP）
  └── parse / trigger / 回写
```

**单体仓多模块**：仓库只对接一次；每张 Issue 用 `service.name` + `module_path` 指定本次模块（gateway / web / bpm…）。

### 建 Issue

复制 [examples/issues/001-order-service-feature.md](../examples/issues/001-order-service-feature.md) 的结构，改成你的模块路径，在 GitHub 创建 Issue。

后续可提供 `scripts/new-issue.sh` 问答生成正文（待做）。

### Cursor 工作流

1. 用 Cursor **打开业务仓**写代码  
2. Agent：「处理 Issue #N」→ `parse_issue`  
3. 改代码、开 PR  
4. 「验货」→ `trigger_pipeline`（优先打你仓库已有 GHA）  
5. 「结案」→ `update_issue_status`

---

## 4. CLI 速查（可选）

```bash
cd mcp-server

# 读单 — 本地文件
uv run python -m opspulse_mcp.tools.parse_issue \
  --file ../examples/issues/001-order-service-feature.md

# 读单 — GitHub
uv run python -m opspulse_mcp.tools.parse_issue \
  --owner OWNER --repo REPO --issue-number N

# 结案 — 预览 Comment
uv run python -m opspulse_mcp.tools.update_issue_status \
  --dry-run --state deployed --service order-service
```

---

## 5. 维护者自测（非用户路径）

仅在开发 OpsPulse 本身时运行：

```bash
./scripts/check-prerequisites.sh
./scripts/e2e-demo.sh    # 使用 internal/dev/local-runner
```

---

## 6. 故障排查

| 现象 | 处理 |
|------|------|
| `ready: false` | 检查 frontmatter；bugfix 需 `## 复现步骤` |
| MCP 未连接 | `uv` 在 PATH；重载 Cursor |
| parse GitHub 404 | Issue 编号或 PAT 权限 |
| 验货只跑本地 | P0：GHA 触发待实现；当前 `mode=local` 走 `internal/dev/` |

---

## 延伸阅读

| 文档 | 说明 |
|------|------|
| [胶水层核心能力](../doc/胶水层核心能力.md) | 产品北极星 |
| [用户接入指南](../doc/用户接入指南.md) | 团队流程与架构 |
| [技术架构](../doc/技术架构.md) | 实现细节 |
| [Harness 配置](./harness-setup.md) | 可选企业 CI |
