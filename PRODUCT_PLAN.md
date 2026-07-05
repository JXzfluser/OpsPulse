# OpsPulse 产品级改造计划

> **目标**：从 demo 级项目 → 真正可用的产品级胶水工具
> **时间**：2026-07-05 起

---

## 一、现状评估

### 已完成（v0.1.0-v0.3.0）
- ✅ MCP 三 Tool（parse_issue / trigger_pipeline / update_issue_status）
- ✅ Issue Spec Schema + 前端 matter 解析
- ✅ GitHub Actions CI 集成
- ✅ `opspulse.sh` 单命令入口
- ✅ 1069 行 Python 代码，结构清晰

### 核心差距（距离产品级）

| 差距 | 说明 | 优先级 |
|------|------|--------|
| **1. 无真实 Issue 联调** | roadmap 中标记 "需真实 Issue + PAT"，说明没跑通端到端 | P0 |
| **2. 本地 Runner 太简陋** | 只是 demo，不支持真实 Java/Maven 项目 | P0 |
| **3. 无 Docker 镜像** | 用户需要手动 `uv sync`，门槛高 | P1 |
| **4. 无 Helm Chart / K8s 部署** | 企业级部署方案缺失 | P2 |
| **5. 文档不完整** | getting-started 缺少截图、常见问题、错误排查 | P1 |
| **6. 测试覆盖不足** | 只有单元测试，缺少 E2E 测试 | P1 |
| **7. 无 CLI 安装包** | `pip install` 或 `brew install` 缺失 | P1 |
| **8. 无监控/日志** | 企业级工具必须有可观测性 | P2 |
| **9. 无多 CI 适配器** | 只支持 GHA，不支持 GitLab CI、Jenkins、Harness | P1 |
| **10. 无 Issue 模板市场** | 用户需要自己写 Issue Spec，缺乏预置模板 | P2 |

---

## 二、改造路线图

### Phase 1：端到端跑通（2 周）

**目标：让第一个真实用户在真实仓库用上**

| 任务 | 产出 |
|------|------|
| 1.1 创建 OpsPulse 官方 Issue 模板 | `.github/ISSUE_TEMPLATE/opspulse-feature.md` |
| 1.2 完善 parse_issue 的 GitHub API 调用 | 支持 `--owner/--repo/--issue` 直接拉取 |
| 1.3 实现本地 Maven 构建 Runner | `local-runner` 支持 `mvn clean verify` |
| 1.4 添加 `opspulse init` 一键初始化 | 在目标仓库生成 `.opspulse/` 配置 |
| 1.5 编写 Getting Started 完整教程 | 含截图、常见错误、FAQ |

### Phase 2：安装与分发（1 周）

**目标：用户 `pip install opspulse` 就能用**

| 任务 | 产出 |
|------|------|
| 2.1 打包为 pip 可安装包 | `setup.py` / `pyproject.toml` |
| 2.2 创建 Docker 镜像 | `opspulse/cli:latest` |
| 2.3 添加 Homebrew Tap | `brew install opspulse` |
| 2.4 编写 CLI 帮助文档 | `opspulse --help` 中文友好 |

### Phase 3：多 CI 适配（2 周）

**目标：支持 GitHub Actions / GitLab CI / Jenkins / Harness**

| 任务 | 产出 |
|------|------|
| 3.1 抽象 CI Adapter 接口 | `BasePipelineAdapter` |
| 3.2 实现 GitLab CI 适配器 | `gitlab_adapter.py` |
| 3.3 实现 Jenkins 适配器 | `jenkins_adapter.py` |
| 3.4 实现 Harness 适配器 | `harness_adapter.py` |
| 3.5 统一 trigger_pipeline 接口 | 自动检测 CI 类型 |

### Phase 4：企业级能力（3 周）

**目标：满足 50-500 人团队需求**

| 任务 | 产出 |
|------|------|
| 4.1 策略引擎完善 | JDK8 底座、Dockerfile 校验、affected_paths 边界 |
| 4.2 组织记忆写入 | 交付记录持久化到 SQLite/PostgreSQL |
| 4.3 监控与日志 | Prometheus metrics + structured logging |
| 4.4 Issue 模板市场 | 预置 5 种模板（Feature/Bugfix/Chore/Hotfix/Refactor） |
| 4.5 多仓库管理 | `opspulse.yaml` 支持 monorepo |

---

## 三、竞品分析

### 直接竞品

| 产品 | 定位 | 差距 | OpsPulse 机会 |
|------|------|------|--------------|
| **GitHub Actions** | CI/CD 平台 | 不提供 Issue→Code→Deploy 闭环 | OpsPulse 填补"意图驱动"空白 |
| **Harness** | 企业级 CI/CD | 贵（enterprise）、重 | OpsPulse 轻量、开源、Java 后端专用 |
| **GitLab CI** | 一体化平台 | 功能全但复杂 | OpsPulse 聚焦 Issue-to-Deploy 单点突破 |
| **Palantir FDE** | 工厂数字化引擎 | 百万美元级 | OpsPulse 让中小团队用得起 |

### 间接竞品

| 产品 | 关系 | 差异化 |
|------|------|--------|
| **Cursor + GitHub Copilot** | 互补 | OpsPulse 管"交付"，Copilot 管"编码" |
| **Jenkins** | 替代 | OpsPulse 更现代、AI-native |
| **ArgoCD** | 互补 | ArgoCD 管"部署"，OpsPulse 管"全流程" |

### 核心差异化

**OpsPulse 不做 CI/CD，不做代码编辑，不做容器编排。**

它只做一件事：**让 Issue 成为交付的唯一入口。**

| 传统流程 | OpsPulse 流程 |
|---------|--------------|
| Issue → 手动分配 → 开发 → PR → 手动触发 CI → 手动部署 | Issue → parse → Agent 开发 → auto CI → auto deploy → auto 回写 |
| 5 步，3 个工具，大量手动操作 | 1 个入口，全自动闭环 |

---

## 四、营销节奏（产品成熟后）

### 阶段 1：产品打磨期（现在 - Phase 3 完成）
- **不做公众号**，专注把产品做好
- GitHub README 就是最好的广告
- 写 3-5 篇技术博客（Medium/知乎/V2EX）讲设计理念

### 阶段 2：早期采用者（Phase 3 完成）
- 在 Hacker News / V2EX / 掘金发介绍帖
- 目标：100 个 Star，10 个 Fork
- 公众号开始发"OpsPulse 开发日志"系列

### 阶段 3：正式推广（Phase 4 完成）
- 公众号每周 1 篇 DevOps 实战
- GitHub Trending 冲刺
- 目标：1000+ Star，企业客户线索

---

## 五、立即行动项

1. **先跑通端到端** — 用自己的 GitHub PAT + 真实 Issue 测试
2. **写好 Getting Started** — 截图 + 步骤 + FAQ
3. **打包 pip install** — 降低试用门槛
