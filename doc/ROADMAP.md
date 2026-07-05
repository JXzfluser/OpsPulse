# OpsPulse 路线图（ROADMAP）

> **当前阶段**：Phase 2 — MVP（Gate 2 本地 E2E 完成）  
> **最后更新**：2026-07-05

---

## 阶段总览

| 阶段 | 时间 | 主题 | 状态 |
|------|------|------|------|
| Phase 0 | 2026-07 W1–W2 | 奠基：文档、前置条件、决策锁定 | 🟡 进行中 |
| Phase 1 | 2026-07 W3–W4 | 骨架：Git 仓库、Schema、Issue 模板 | 🟡 代码完成，Gate 1 待验证 |
| Phase 2 | 2026-08 W1–W4 | MVP：MCP + 流水线 + E2E | 🟢 Gate 2 本地验收通过 |
| Phase 3 | 2026-09 – 11 | 发布：v0.1–v0.3、内容冷启动 | ⬜ 待开始 |
| Phase 4 | 2026-12 – 2027-05 | 增长：Pro 插件、商业化 | ⬜ 待开始 |
| Phase 5 | 2027-06 – 2027-07 | 成熟：v2.0、社区、企业定制 | ⬜ 待开始 |

---

## Phase 0：奠基（W1–W2）

| 任务 | 产出 | 状态 |
|------|------|------|
| 项目宪章 | `doc/PROJECT_CHARTER.md` | ✅ |
| 整体规划 | `doc/OpsPulse整体项目规划.md` | ✅ |
| 前置条件 | `doc/PREREQUISITES.md` | ✅ |
| 决策锁定 | `doc/DECISIONS.md` | ✅ |
| FDE 方法论 | `doc/FDE方法论.md` | ✅ |
| 技术架构 | `doc/技术架构.md` | ✅ |
| 需求池模板 | `doc/需求池.md` | ✅ |
| KPI 模板 | `doc/KPI.md` | ✅ |
| 竞品分析 | `doc/竞品分析.md` | ✅ |
| 验证脚本 | `scripts/check-prerequisites.sh` | ✅ |
| 实施计划 | `doc/实施计划.md` | ✅ |
| 用户接入指南 | `doc/用户接入指南.md` | ✅ |
| 环境验证 | 本地 Python/Docker（无需 Java） | ⬜ |
| 用户访谈 #1 | `doc/interviews/001.md` | ⬜ |
| Gate 0 通过 | PREREQUISITES 清单全绿 | ⬜ |

---

## Phase 1：骨架（W3–W4）

- [x] 初始化 Git 仓库（`git init` 完成；GitHub remote 待人工添加）
- [x] `README.md`（定位 + 架构 + 快速开始）
- [x] `LICENSE`（Apache-2.0）+ `CONTRIBUTING.md`
- [x] `.github/ISSUE_TEMPLATE/` + PR 模板
- [x] `schemas/issue-spec.v1.json` + `scripts/validate-issue-spec.py` + 单元测试
- [x] `examples/issues/`（3 个预置场景，本地 Schema 校验通过）
- [x] `.env.example` + `.gitignore` + `opspulse.yaml`
- [x] `.github/workflows/validate-schema.yml`（CI 工作流已创建）
- [x] `harness-templates/` + `local-runner/` 流水线骨架
- [x] `.cursor/mcp.json` + `prompts/` + `docs/mcp-setup.md` + `docs/harness-setup.md`
- [x] `examples/fixtures/`（JDK8 Dockerfile + README）
- [x] `CHANGELOG.md` v0.0.1-schema
- [ ] `git push` + GitHub 上 Issue 模板可选（Gate 1 人工项）
- [ ] `validate-schema.yml` CI 在 GitHub 绿（需 push 后验证）

**Gate 1**：Schema CI 校验通过；Issue 模板可在 GitHub 创建 — **本地验收通过，远程待 push**

---

## Phase 2：MVP（W5–W8）

| 周 | 交付 | 验收 |
|----|------|------|
| W5 | `opspulse-mcp` + `parse_issue` | ✅ 3 个预置 Issue 解析正确 |
| W6 | `update_issue_status` + github-mcp 联调 | ✅ Comment 模板 + dry-run CLI；GitHub 联调待 PAT |
| W7 | `trigger_pipeline` + `local-runner`（镜像模式） | ✅ pr-validation 本地通过（Docker 可选） |
| W8 | deploy-dev + quickstart.md | ✅ `scripts/e2e-demo.sh` + `docs/quickstart.md` |

**Gate 2**：Issue #1 全链路跑通（parse → 镜像流水线 → comment）；README 第三人可复现 — **本地 E2E 通过**

> **不含 sample-backend**：E2E 用 `examples/issues/` + 基础镜像冒烟演示（见 D11）。

---

## Phase 3：发布与冷启动（M3–M6）

### v0.1.0（M3）
- 开源发布
- 公众号文章 1
- Star 目标 ≥ 30

### v0.2.0（M4）
- `parse_issue` 增强（更多标签 fallback）
- 文章 2

### v0.3.0（M5–M6）
- Harness Remote Template 实机验证
- 文章 3
- 社群启动
- Star 目标 ≥ 100

---

## Phase 4：增长与变现（M6–M12）

- `opspulse-pro` 规格发布
- Multi-Env Pack 内测
- 9.9 资料包 + 99 元社群
- `init-ai`（遗留 Java + Cursor/MCP）预研
- 产品化率 ≥ 0.3；首笔付费；月入 3k+

---

## Phase 5：成熟与共建（M12–M24）

- v2.0 完整流水线
- 社区贡献者指南
- 企业定制（5k–30k/项目）
- 产品化率 ≥ 0.5；Star ≥ 2000

---

## 版本发布计划

| 版本 | 预计时间 | 核心内容 |
|------|----------|----------|
| v0.1.0 | M3 | MCP 三 Tool + local-runner（镜像模式）+ Issue 样例 |
| v0.2.0 | M4 | Issue 解析增强 + GHA workflow |
| v0.3.0 | M6 | Harness 模板实机 + deploy-dev |
| v0.4.0 | M8 | Pro Multi-Env Pack 内测 |
| v1.0.0 | M12 | 稳定版 + 文档完善；可选 JDK8 sample-backend |
| v2.0.0 | M24 | 社区共建 + 插件生态 |

---

## 不在 Roadmap 内（明确放弃）

- ES 运维脚本生成器（已由 Issue-to-Deploy 替代）
- SpringBoot 全量脚手架
- 代码格式化独立工具
- 通用 AI 编辑器测评内容
