# OpsPulse 前置设定条件

> 本文档列出项目启动前必须满足的条件。**Gate 0 全部打勾后，才可进入 Phase 1 写代码。**

---

## 1. 角色与精力设定

| 设定项 | 最低要求 | 推荐值 | 不满足则 |
|--------|----------|--------|----------|
| 角色 | 1 人，≥ 15h/周 | Solo，20–25h/周 | 里程碑顺延 1.5× |
| Java 后端经验 | ≥ 3 年 | 熟悉 JDK8 遗留项目 + CI/CD + 基础镜像发布 | 不扩展业务代码演示 |
| 用户对话 | ≥ 1 次/周 | ≥ 2 次/周，30min/次 | P0 需求不做 |
| 内容节奏 | 双周 1 篇 | 双周 1 篇深度实战 | 不日更、不追热点 |

---

## 2. 账号与平台清单

| 平台 | 用途 | 状态 | 必须/可选 |
|------|------|------|-----------|
| GitHub | 开源仓库、Issue、Actions、MCP | ✅ 仓库已 push（[JXzfluser/OpsPulse](https://github.com/JXzfluser/OpsPulse)） | **必须** |
| GitHub PAT | MCP + API 访问（`repo`, `workflow`） | ⬜ 待完成 | **必须** |
| Cursor | AI Agent + MCP 宿主 | ⬜ 待完成 | **必须** |
| Docker Desktop | github-mcp-server 本地运行 | ⬜ 待完成 | **必须** |
| 微信公众号 | 内容引流 | ⬜ 待完成 | **必须**（M1 前） |
| Harness | 企业 CI/CD 模板验证 | ⬜ 待完成 | 可选（M2 前） |
| 掘金/知乎 | 内容分发 | ⬜ 待完成 | 可选 |
| 飞书/微信群 | 私域社群 | ⬜ 待完成 | M3 前 |
| 域名 | 品牌页 | ⬜ 待完成 | M6 前 |

### GitHub PAT 所需 Scope

- `repo`（读写仓库、Issue、PR）
- `workflow`（触发 GitHub Actions）
- `read:org`（若使用 org 仓库）

---

## 3. 本地开发环境

| 依赖 | 版本要求 | 验证命令 | 状态 |
|------|----------|----------|------|
| macOS / Linux | — | — | ✅ darwin |
| Git | ≥ 2.40 | `git --version` | ✅ 2.52.0 |
| Python | ≥ 3.11 | `python3 --version` | ✅ 3.14.4 |
| uv | 最新 | `uv --version` | ✅ 0.10.7 |
| Docker | ≥ 24 | `docker info` | ✅ OrbStack（2026-07-05 全链路验证） |
| Java（JDK） | — | — | **不要求**（MVP 无 sample-backend） |
| Maven | — | — | **不要求** |
| Node.js | ≥ 20 | `node --version` | ✅ v22.23.1（可选） |

> **说明**：
> - **目标用户侧**：JDK 1.8 **微服务**仓库，通常有 Maven/Gradle + 企业 **JDK8 运行时基础镜像**（非整应用镜像）。
> - **OpsPulse 工具链侧**（本仓库开发）：Python + Docker 即可；**无需**在 OpsPulse 仓内放 `sample-backend`（D11）。
> - 流水线模板设计为**接入用户微服务仓库**使用，而非在 OpsPulse 内嵌完整业务工程。

**一键验证**：运行项目根目录 `scripts/check-prerequisites.sh`（✅ Phase 1 已创建）

---

## 4. 密钥与配置管理

| 密钥 | 存放位置 | 禁止 |
|------|----------|------|
| `GITHUB_PAT` | `.env`（已 gitignore） | 提交到仓库 |
| `HARNESS_API_KEY` | `.env` | 写入开源模板 |
| AI API Key | Cursor 内置或 `.env` | 硬编码到 Prompt |

**Phase 1 将创建**：

- `.env.example`（变量名列表，无真实值）
- `.gitignore`
- `opspulse.yaml`（非敏感全局配置）

---

## 5. 法律与合规

| 项 | 动作 | 状态 |
|----|------|------|
| 开源 LICENSE | Apache-2.0（Phase 1） | ✅ |
| 商标 | 暂不注册 | — |
| 用户数据 | 不收集；MCP 仅读公开 Issue | — |
| 企业咨询合同 | M6 前准备模板 | ⬜ |

---

## 6. Gate 0 退出清单

**全部 ⬜ → ✅ 才可进入 Phase 1：**

- [ ] [PROJECT_CHARTER.md](./PROJECT_CHARTER.md) 已创建并确认
- [ ] 本文档账号/环境项已逐项验证
- [ ] `scripts/check-prerequisites.sh` 执行通过（脚本已就绪：`./scripts/check-prerequisites.sh`）
- [ ] [DECISIONS.md](./DECISIONS.md) 9 项决策已锁定
- [ ] GitHub 账号 + PAT 已就绪
- [ ] Cursor + Docker 可启动 github-mcp-server
- [ ] [需求池.md](./需求池.md) 模板已创建
- [ ] 已完成 ≥ 1 次目标用户访谈（记录到 `doc/interviews/`）
- [ ] 微信公众号已注册（可不发文）

### Gate 0 完成记录

| 项 | 完成日期 | 备注 |
|----|----------|------|
| 规划文档输出 | 2026-07-05 | 本次 |
| 环境验证 | 2026-07-05 | 全测试绿；Docker 镜像阶段 OK；`check-prerequisites.sh` 通过 |
| 用户访谈 #1 | | |
| GitHub remote push | 2026-07-05 | `main` @ 6931a54+；tag `v0.1.0-demo` |
| Gate 0 通过 | | |

---


---

## 8. Gate 1 状态（Phase 1 骨架）

| 项 | 状态 | 备注 |
|----|------|------|
| 初始 commit + push `main` | ✅ | https://github.com/JXzfluser/OpsPulse |
| `validate-schema.yml` CI | ✅ | `b8e14e8` — Validate Issue Spec success |
| Issue 模板在 GitHub 可用 | 🟡 待人工确认 | 仓库 Settings → Features |
| 本地 Schema 校验 | ✅ | `python3 scripts/validate-issue-spec.py examples/issues/*.md` |

## 7. 常见问题

**Q：没有 Harness 账号能开始吗？**  
A：能。默认 CI 用 local-runner + GitHub Actions；Harness 为 M2 可选验证。

**Q：Windows 可以吗？**  
A：建议 WSL2；原生 Windows 不在首版支持范围。

**Q：没有公众号能进 Phase 1 吗？**  
A：能。但 Phase 3 发布前必须完成注册。
