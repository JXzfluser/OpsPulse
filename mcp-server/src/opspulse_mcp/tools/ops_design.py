"""设计方案生成 Tool — 基于 Issue Spec 自动生成技术方案"""
from __future__ import annotations

import json
from typing import Any

from opspulse_mcp.github.client import create_issue_comment
from opspulse_mcp.workflow import IssueWorkflow


def ops_design(
    issue_number: int,
    issue_spec: dict[str, Any],
    owner: str | None = None,
    repo: str | None = None,
) -> dict[str, Any]:
    """根据 Issue Spec 自动生成技术方案。

    生成内容包括：
    - 数据库变更（如果有）
    - API 变更（如果有）
    - 配置变更
    - 依赖变更
    - 风险评估

    Args:
        issue_number: GitHub Issue 编号
        issue_spec: parse_issue 输出的 spec
        owner: GitHub owner
        repo: GitHub repo name

    Returns:
        设计文档 + 状态转移结果
    """
    service = issue_spec.get("service", {})
    service_name = service.get("name", "unknown")
    build = issue_spec.get("build", {})
    deploy = issue_spec.get("deploy", {})
    acceptance = issue_spec.get("acceptance", [])
    affected_paths = issue_spec.get("affected_paths", [])

    # 生成设计文档
    design_doc = f"""# 技术方案: {service_name}

## 1. 变更概述
- **服务**: {service_name}
- **模块路径**: {service.get('module_path', 'N/A')}
- **构建工具**: {build.get('tool', 'N/A')}
- **部署环境**: {deploy.get('env', 'N/A')}

## 2. 受影响文件
"""
    for path in affected_paths:
        design_doc += f"- `{path}`\n"

    design_doc += f"""
## 3. 验收标准
"""
    for ac in acceptance:
        design_doc += f"- **{ac.get('id', '?')}**: {ac.get('given', '')} → {ac.get('then', '')}\n"

    design_doc += f"""
## 4. 风险评估
- **影响范围**: {len(affected_paths)} 个路径
- **回归风险**: {'中' if len(affected_paths) > 3 else '低'}
- **回滚方案**: 保留上一版本镜像，快速切换

## 5. 部署计划
1. 构建: `{build.get('command', 'N/A')}`
2. 产物: `{build.get('artifact', 'N/A')}`
3. 镜像: `{deploy.get('image', 'N/A')}`
4. 部署: `deploy/{service_name}/Dockerfile`
"""

    # 状态转移
    workflow = IssueWorkflow(issue_number, owner or "JXzfluser", repo or "OpsPulse")
    success = workflow.transition("design")
    comment = f"""## OpsPulse 设计方案

**状态**: {workflow.current()}
**转移**: {'✅ 成功' if success else '❌ 失败'}

```markdown
{design_doc}
```
"""

    # 发布 Comment
    posted = False
    if owner and repo:
        try:
            comment_data = create_issue_comment(owner, repo, issue_number, comment)
            posted = True
        except Exception:
            pass

    return {
        "issue_number": issue_number,
        "design_doc": design_doc,
        "transition": {
            "success": success,
            "from": "REVIEW_PASS",
            "to": "DESIGN_PENDING",
        },
        "posted": posted,
        "workflow": workflow.history_summary(),
    }
