# OpsPulse 整体项目规划

> **版本**：v1.0.0  
> **日期**：2026-07-05  
> **状态**：Phase 0 — 奠基中  
> **定位**：Issue-to-Deploy 虚拟 FDE 开源脚手架（MCP + GitHub Issue + Harness CI/CD）

本文档是 OpsPulse 项目的**总纲**。执行任何开发任务前，必须先完成 [PREREQUISITES.md](./PREREQUISITES.md) 中的 Gate 0 检查。

---

## 文档索引

| 文档 | 用途 |
|------|------|
| [PROJECT_CHARTER.md](./PROJECT_CHARTER.md) | 项目宪章：使命、愿景、资产形态 |
| [PREREQUISITES.md](./PREREQUISITES.md) | 前置设定条件 + Gate 0 清单 |
| [DECISIONS.md](./DECISIONS.md) | 9 项锁定决策（不可摇摆） |
| [FDE方法论.md](./FDE方法论.md) | 虚拟 FDE + 土路铺高速 + 产品化率 |
| [技术架构.md](./技术架构.md) | MCP / Issue 契约 / Harness 流水线完整设计 |
| [ROADMAP.md](./ROADMAP.md) | 24 个月分阶段路线图 |
| [需求池.md](./需求池.md) | 需求入库模板与治理规则 |
| [KPI.md](./KPI.md) | 指标金字塔与复盘模板 |
| [竞品分析.md](./竞品分析.md) | 竞品速览与差异化 |
| [content/文章1大纲.md](./content/文章1大纲.md) | 公众号首发文章大纲 |
| [实施计划.md](./实施计划.md) | **Phase 0–2 详细实施计划（执行入口）** |
| [用户接入指南.md](./用户接入指南.md) | **如何介入用户项目 + 与 Cursor 差异** |

---

## 一、项目定义

| 项 | 内容 |
|----|------|
| **项目名** | OpsPulse |
| **Slogan** | `Describe in Issue, Ship via Harness.` |
| **一句话** | Java 后端团队的 Issue-to-Deploy 虚拟 FDE 开源脚手架 |
| **目标用户** | 50–500 人 Java 团队 TL/平台工程师（有 GitHub + CI/CD，Issue→上线链路断裂） |
| **非目标用户** | 无 CI/CD 基建小团队、纯前端、已自建 IDP 的大厂 |

### 商业模式（唯一闭环）

```
虚拟前线嵌入（Issue/社群/咨询）
  → 痛点验证
  → 开源工具 Day1 交付
  → 公众号实战内容
  → GitHub Star + 私域
  → 分层商业化
  → 需求回流 + 资产沉淀（产品化率 ≥ 0.5）
```

---

## 二、核心场景架构

```
GitHub Issue（交付契约）
  → MCP 解析（parse_issue）
  → Cursor Agent 开发
  → Pull Request
  → CI/CD 验证（GHA / local-runner / Harness）
  → 部署 Dev 环境
  → Issue 状态回写（update_issue_status）
  → 企业定制 48h 抽象为开源模板（FDE 沉淀）
```

详细设计见 [技术架构.md](./技术架构.md)。

---

## 三、产品分层

### 开源免费（`opspulse`）

- Issue Spec Schema + GitHub Issue 模板
- MCP 三核心 Tool：`parse_issue` / `trigger_pipeline` / `update_issue_status`
- Harness PR 验证 + Dev 部署模板
- local-runner + GitHub Actions
- Spring Boot 示例后端 + Agent Prompts

> **修订（D11/D12）**：MVP **暂缓 `sample-backend`**（不在 OpsPulse 仓内置微服务工程）。目标用户为 **JDK 1.8 微服务** + 企业 **JDK8 运行时基础镜像**；流水线 = 底座校验 → 微服务 build → 服务镜像 → 部署。

### 付费增值（`opspulse-pro`）

| 插件包 | 定价 | 能力 |
|--------|------|------|
| Multi-Env Pack | 99 元/年 | Staging/Prod 晋升 + 审批门禁 |
| Connector Pack | 199 元专栏 | 钉钉/飞书/Jira/Nexus |
| Compliance Pack | 企业 5k+ | Sonar/漏洞/许可证扫描 |
| Routing Pack | 咨询交付 | 多团队路由 + SLA |
| Offline Bundle | 999 元/套 | 离线 MCP + 模板包 |

**硬边界**：免费版 = Issue → PR → 测试通过；付费版 = 多环境 + 审批 + 合规。

---

## 四、24 个月阶段路线

| 阶段 | 时间 | 主题 | Gate 退出标准 |
|------|------|------|---------------|
| **Phase 0** | W1–W2 | 奠基 | Gate 0 全通过 |
| **Phase 1** | W3–W4 | 仓库骨架 + Issue 契约 | Schema CI 绿 |
| **Phase 2** | W5–W8 | MCP + 流水线 + E2E | Issue #1 全链路跑通 |
| **Phase 3** | M3–M6 | 开源发布 + 内容冷启动 | Star ≥ 30；TTFV < 30min |
| **Phase 4** | M6–M12 | Pro 插件 + 商业化 | 产品化率 ≥ 0.3；首笔付费 |
| **Phase 5** | M12–M24 | 社区共建 + 企业定制 | 产品化率 ≥ 0.5 |

详见 [ROADMAP.md](./ROADMAP.md)。

---

## 五、KPI 优先级

1. **一级**（决策用）：产品化率 ≥ 0.5、TTFV < 15min、Day1 交付率 ≥ 80%
2. **二级**（健康度）：GitHub Star、活跃 Issue、Fork
3. **三级**（商业）：月收入、付费用户、社群人数

详见 [KPI.md](./KPI.md)。

**6 个月 Pivot 线**：Star < 30 且产品化率 < 0.2 → 自我评审，考虑场景 pivot。

---

## 六、运营节奏（永久 SOP）

| 频率 | 动作 |
|------|------|
| **每日** ≤15min | 扫 GitHub 反馈；记 1 条需求候选 |
| **每周三前** | 交付 1 个可运行增量 |
| **每周四** | 用户对话 1 次（30min） |
| **每周五** | 更新需求池；记录产品化率；写周报 |
| **每月** | 发版本 tag；更新 Roadmap；复盘 KPI |

时间分配：发现 30% / 构建 40% / 交付 15% / 传播 10% / 产品化 5%

---

## 七、FDE 资产沉淀规则

| 层级 | 定义 | 存放 |
|------|------|------|
| **L1 开源** | 80%+ 团队可复用 | `opspulse` 主仓库 |
| **L2 可配置** | YAML 扩展点适配 | `opspulse.yaml` + `schemas/extensions/` |
| **L3 企业定制** | 客户私有逻辑 | 客户 fork / `opspulse-pro` |

**产品化率** = L1/L2 抽象数 / L3 交付数。每次 L3 交付后 **48h 内**评估抽象。详见 [FDE方法论.md](./FDE方法论.md)。

---

## 八、风险登记册

| ID | 风险 | 缓解 |
|----|------|------|
| R1 | 单人精力不足 | 严格 Phase Gate；不并行多 MVP |
| R2 | MCP 生态变动 | REST CLI fallback |
| R3 | Harness 受众窄 | GHA 为默认；Harness 为企业可选 |
| R4 | AI 代码质量差 | `ready` 门禁 + `affected_paths` + 人工 Review |
| R5 | 定制吞噬产品化 | 产品化率 < 0.2 停接定制 |
| R6 | 内容无引流 | 每篇绑定可运行 tag |
| R7 | 跳过前置条件 | Gate 0 强制 |

---

## 九、执行入口

```
当前位置：Phase 0（规划完成，待 Gate 0）

执行文档：doc/实施计划.md

下一步：
  1. 完成 PREREQUISITES.md Gate 0 清单
  2. 运行 scripts/check-prerequisites.sh
  3. 完成 ≥1 次用户访谈（doc/interviews/001.md）
  4. Gate 0 通过 → 按实施计划 §3 进入 Phase 1
  5. 说「开始 Phase 1」启动仓库初始化
```

---

## 十、与原规划文档关系

本规划替代原 [FDE垂直DevOps AI开源项目｜24个月可落地完整规划文档（无虚、全执行）.md](./FDE垂直DevOps%20AI开源项目｜24个月可落地完整规划文档（无虚、全执行）.md) 中的执行层内容：

- **保留**：垂直赛道定力、FDE 闭环思想、内容-产品绑定、避坑清单
- **替换**：ES 运维 MVP → Issue-to-Deploy 脚手架
- **新增**：前置条件 Gate、决策锁定、技术架构、产品分层、虚拟 FDE 方法论
