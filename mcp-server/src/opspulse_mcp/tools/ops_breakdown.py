"""任务拆分 Tool — 将 Issue 拆分为可执行的小任务"""
from __future__ import annotations

import json
from typing import Any

from opspulse_mcp.github.client import create_issue_comment
from opspulse_mcp.workflow import IssueWorkflow


def ops_breakdown(
    issue_number: int,
    issue_spec: dict[str, Any],
    design_doc: str,
    owner: str | None = None,
    repo: str | None = None,
) -> dict[str, Any]:
    """将 Issue 拆分为可执行的任务列表。"""
    service = issue_spec.get("service", {})
    service_name = service.get("name", "unknown")
    acceptance = issue_spec.get("acceptance", [])
    affected_paths = issue_spec.get("affected_paths", [])

    tasks = []
    task_id = 1

    for path in affected_paths:
        tasks.append({
            "id": f"T-{task_id:03d}",
            "type": "code",
            "title": f"修改: {path}",
            "description": f"根据 Issue #{issue_number} 的需求，修改 {path}",
            "depends_on": [],
            "status": "pending",
        })
        task_id += 1

    for ac in acceptance:
        tasks.append({
            "id": f"T-{task_id:03d}",
            "type": "test",
            "title": f"验证: {ac.get('id', '?')}",
            "description": f"验证 acceptance: {ac.get('given', '')} → {ac.get('then', '')}",
            "depends_on": [],
            "status": "pending",
        })
        task_id += 1

    tasks.append({
        "id": f"T-{task_id:03d}",
        "type": "deploy",
        "title": f"部署: {service_name} to {issue_spec.get('deploy', {}).get('env', 'dev')}",
        "description": f"部署 {service_name} 到 {issue_spec.get('deploy', {}).get('env', 'dev')} 环境",
        "depends_on": [f"T-{task_id-1:03d}"],
        "status": "pending",
    })

    tasks_md = "| ID | 类型 | 标题 | 状态 |\n|-----|------|------|------|\n"
    for t in tasks:
        tasks_md += f"| {t['id']} | {t['type']} | {t['title']} | {t['status']} |\n"

    workflow = IssueWorkflow(issue_number, owner or "JXzfluser", repo or "OpsPulse")
    success = workflow.transition("breakdown")

    comment = f"""## OpsPulse 任务拆分

**状态**: {workflow.current()}
**转移**: {'✅ 成功' if success else '❌ 失败'}

### 任务列表

{tasks_md}

### 依赖关系

"""
    for t in tasks:
        dep = ", ".join(t["depends_on"]) if t["depends_on"] else "无"
        comment += f"- {t['id']} → {dep}\n"

    posted = False
    if owner and repo:
        try:
            create_issue_comment(owner, repo, issue_number, comment)
            posted = True
        except Exception:
            pass

    return {
        "issue_number": issue_number,
        "tasks": tasks,
        "tasks_markdown": tasks_md,
        "transition": {"success": success, "from": "DESIGN_APPROVED", "to": "BREAKDOWN_DONE"},
        "posted": posted,
        "workflow": workflow.history_summary(),
    }
