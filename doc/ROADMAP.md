# OpsPulse 路线图（ROADMAP）

> **定位**：真胶水层 — 三动词、零侵入、四引擎。  
> **当前**：v0.1.0-demo 完成；进入 **v0.2.0 胶水收敛** 重构。  
> **最后更新**：2026-07-05

---

## 版本策略

| 版本 | 主题 | 用户可感知变化 |
|------|------|----------------|
| **v0.1.0-demo** | MVP 能力验证 | MCP 三 Tool + Issue Schema + 开发自测流水线 |
| **v0.2.0** | **胶水收敛** | 删冗余脚本/文档；`internal/` 收纳；单一 getting-started |
| **v0.3.0** | **真 CI 闭环** | `trigger_pipeline` → GHA `workflow_dispatch` |
| **v0.4.0** | **真回写** | `update_issue_status` post GitHub Comment |
| **v1.0.0** | 生产可用 | 策略引擎 + `opspulse handle #N` 单命令 |

---

## v0.2.0 胶水收敛（当前）

| 任务 | 状态 |
|------|------|
| 删除 bootstrap / onboard / remove-bootstrap 脚本 | ✅ |
| `local-runner` + `fixtures` → `internal/dev/` | ✅ |
| `harness-templates` → `internal/optional/` | ✅ |
| 用户文档合并为 `docs/getting-started.md` | ✅ |
| 规划文档归档 `doc/internal/` | ✅ |
| README 重写（三动词入口） | ✅ |

---

## v0.3.0 真 CI 闭环（P0）— 进行中

| 任务 | 状态 |
|------|------|
| `trigger_pipeline` 支持 `mode=github-actions` | ✅ workflow_dispatch |
| Issue Spec `repository` + `ci` 字段 | ✅ |
| `opspulse.yaml` 仓库 workflow 映射 | ✅ |
| `update_issue_status` post GitHub Comment | ✅ |
| `scripts/opspulse.sh handle` 单命令 | ✅ |
| chuanplus-platform 实仓联调 | ⬜ 需真实 Issue + PAT |

---

## v0.4.0 真回写（P1）

| 任务 | 状态 |
|------|------|
| `update_issue_status` 调用 GitHub API 发 Comment | ✅（v0.3 提前交付） |
| `new-issue.sh` 问答生成 Issue 正文 | ⬜ |

---

## v1.0.0 策略与单命令（P2）

| 任务 | 验收 |
|------|------|
| JDK8 底座策略进 parse | 违规 `ready=false` |
| `affected_paths` 策略校验 | Agent 边界可强制 |
| `opspulse handle --issue N --repo owner/name` | 封装三动词 |
| TTFV < 15min（第三人） | 仅 getting-started 一条路径 |

---

## 明确不做

- 每业务仓 bootstrap 一整套 OpsPulse 文件  
- `sample-backend/` 进本仓（D11）  
- local-runner 作为用户默认 CI  
- 替代 Cursor / 替代客户 Harness（仅适配）

---

## 文档索引

| 读者 | 文档 |
|------|------|
| 用户 | `docs/getting-started.md` |
| 产品 | `doc/胶水层核心能力.md` |
| 架构 | `doc/技术架构.md` |
| 历史规划 | `doc/internal/` |
