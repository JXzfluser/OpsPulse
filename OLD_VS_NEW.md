# OpsPulse 新旧设计对比

## 核心问题

> 用户自己使用 AI 进行对话编程，和使用这个项目的门槛是不是拉高了？

**答案是：是的。** 旧设计要求用户主动使用 MCP 工具，门槛太高。

---

## 旧设计（MCP 驱动）

```
用户必须：
1. 配置 GITHUB_PAT
2. 安装 MCP Server
3. 配置 Cursor MCP
4. 手动调用 parse_issue
5. 手动调用 trigger_pipeline
6. 手动调用 update_issue_status
```

**问题：**
- 用户需要记住 11 个工具名
- 每个工具需要不同的参数
- 配置复杂，出错难排查
- 认知负担重

---

## 新设计（CLI 驱动）

```
用户只需要：
1. 配置 GITHUB_PAT（一次）
2. 说一句话：opspulse handle --issue 45
3. 等着看结果
```

**优势：**
- 只有 4 个命令：new, handle, review, log
- handle 一条命令走完全流程
- 参数有默认值，大多数情况只需传 issue number
- 出错时有清晰的错误提示

---

## 能力对比

| 能力 | 旧设计 | 新设计 |
|------|--------|--------|
| Issue 创建 | 手动写 YAML frontmatter | 交互式引导 |
| Spec 解析 | parse_issue 手动调用 | handle 自动调用 |
| 方案生成 | ops_design 手动调用 | handle 自动调用 |
| 任务拆分 | ops_breakdown 手动调用 | handle 自动调用 |
| PR 创建 | ops_create_pr 手动调用 | handle 自动调用 |
| CI 触发 | trigger_pipeline 手动调用 | handle 自动调用 |
| 状态回写 | update_issue_status 手动调用 | handle 自动调用 |
| 交付日志 | 无 | log 命令 |

**结论：所有能力都保留，只是调用方式从「手动」变成了「自动」。**

---

## 适用场景

| 场景 | 推荐方式 |
|------|----------|
| 个人快速迭代 | CLI（`opspulse handle`） |
| 团队标准化流程 | CLI + MCP 混合 |
| AI Agent 自动编排 | MCP（11 个工具） |
| 新手入门 | CLI（4 个命令够用了） |

---

## 迁移路径

```
旧: 用户 → 学 MCP → 手动调工具
新: 用户 → 学 4 个命令 → 一条命令走完全流程
```

**代码不用改**，CLI 和 MCP 共享底层能力，只是调用入口不同。
