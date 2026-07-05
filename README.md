# OpsPulse

**Issue 下单，流水线验货，Comment 结案。**

面向 JDK 1.8 微服务团队的 **Issue-to-Deploy 胶水层** — 在 GitHub Issue、Cursor Agent 与你已有 CI 之间提供契约、编排与闭环。

- 不替代 Cursor、不侵入业务仓、不重建 JDK8 底座  
- 用户侧：**三个动词**（读单 / 验货 / 结案）  
- 系统侧：**四引擎**（契约编译、策略、编排、组织记忆）

> 北极星：[胶水层核心能力](doc/胶水层核心能力.md) · 上手：[快速上手](docs/getting-started.md)

---

## 三个动词

| 动词 | 你说 | 系统做 |
|------|------|--------|
| **读单** | 「处理 Issue #45」 | 校验工单 → 输出可执行 Spec → `ready` 门禁 |
| **验货** | 「跑 pr-validation」 | 编排 CI 阶段 → 汇总结果 |
| **结案** | 「回写 Issue」 | 状态 + 验收 ✅❌ → Comment |

**配置一次**：`GITHUB_PAT` + Cursor MCP（见 [getting-started](docs/getting-started.md)）。  
**业务仓**：零 OpsPulse 文件。

---

## 仓库结构

```
OpsPulse/
├── mcp-server/          # 核心：parse_issue · trigger_pipeline · update_issue_status
├── schemas/             # Issue Spec 契约
├── examples/issues/     # 工单样例（仅参考）
├── prompts/             # Agent 指令
├── .cursor/             # MCP 配置
├── docs/                # 用户文档
├── internal/            # 维护者自测（local-runner、fixtures）— 不对用户曝光
└── doc/                 # 产品与架构文档
```

---

## 快速开始

```bash
cp .env.example .env && cd mcp-server && uv sync --extra dev
./scripts/opspulse.sh handle --owner OWNER --repo REPO --issue N --verify
```

然后打开 [docs/getting-started.md](docs/getting-started.md)。对 Agent 说：**「处理 Issue #N」**。

维护者自测：`./scripts/e2e-demo.sh`（`internal/dev/`）。

---

## 文档

| 文档 | 读者 |
|------|------|
| [快速上手](docs/getting-started.md) | **所有人** |
| [胶水层核心能力](doc/胶水层核心能力.md) | 产品 / 架构 |
| [用户接入指南](doc/用户接入指南.md) | 团队落地 |
| [MCP 配置](docs/mcp-setup.md) | Cursor 联调 |
| [路线图](doc/ROADMAP.md) | 版本计划 |

规划与历史文档见 `doc/internal/`。

---

## License

Apache-2.0 — [LICENSE](LICENSE)
