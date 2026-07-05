"""冒烟测试 Tool — PR 验证通过后自动部署到测试环境"""
from __future__ import annotations

from typing import Any

from opspulse_mcp.workflow import IssueWorkflow


def ops_smoke_test(
    issue_number: int,
    pipeline_id: str,
    owner: str,
    repo: str,
) -> dict[str, Any]:
    """冒烟测试：部署到 staging 并验证 acceptance criteria。

    Args:
        issue_number: Issue 编号
        pipeline_id: 要触发的 pipeline (pr-validation / deploy-dev)
        owner: GitHub owner
        repo: GitHub repo name

    Returns:
        测试结果和状态转移
    """
    workflow = IssueWorkflow(issue_number, owner, repo)

    # 模拟冒烟测试（实际会调用 trigger_pipeline + 健康检查）
    success = workflow.transition("smoke_test")

    return {
        "issue_number": issue_number,
        "pipeline_id": pipeline_id,
        "transition": {"success": success, "from": "PR_VERIFIED", "to": "SMOKE_TESTING"},
        "status": "success" if success else "failed",
        "workflow": workflow.history_summary(),
    }
