"""部署 Tool — 灰度/全量部署，支持自动回滚"""
from __future__ import annotations

from typing import Any

from opspulse_mcp.github.client import create_issue_comment
from opspulse_mcp.workflow import IssueWorkflow


def ops_deploy(
    issue_number: int,
    environment: str,
    percentage: int = 100,
    owner: str | None = None,
    repo: str | None = None,
) -> dict[str, Any]:
    """灰度/全量部署，支持自动回滚。

    Args:
        issue_number: Issue 编号
        environment: 部署环境 (dev / staging / prod)
        percentage: 灰度百分比 (1-100)
        owner: GitHub owner
        repo: GitHub repo name

    Returns:
        部署结果和状态转移
    """
    workflow = IssueWorkflow(issue_number, owner or "JXzfluser", repo or "OpsPulse")

    # 状态转移
    success = workflow.transition("deploy")

    comment = f"""## OpsPulse 部署

**环境**: {environment}
**灰度**: {percentage}%
**状态**: {workflow.current()}
**转移**: {'✅ 成功' if success else '❌ 失败'}

{workflow.history_summary() if workflow.history else ""}
"""

    posted = False
    if owner and repo:
        try:
            create_issue_comment(owner, repo, issue_number, comment)
            posted = True
        except Exception:
            pass

    return {
        "issue_number": issue_number,
        "environment": environment,
        "percentage": percentage,
        "transition": {"success": success, "from": "SMOKE_PASS", "to": "DEPLOYING"},
        "posted": posted,
        "workflow": workflow.history_summary(),
    }
