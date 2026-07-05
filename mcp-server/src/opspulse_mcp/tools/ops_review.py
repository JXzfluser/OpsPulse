"""需求评审 Tool — Issue 创建后自动评审"""
from __future__ import annotations

import json
import os
from typing import Any

from opspulse_mcp.github.client import create_issue_comment
from opspulse_mcp.workflow import IssueWorkflow


def ops_review(
    issue_number: int,
    reviewer: str,
    approved: bool,
    comments: str,
    owner: str | None = None,
    repo: str | None = None,
) -> dict[str, Any]:
    """需求评审：检查 Issue 完整性并给出评审意见。

    Args:
        issue_number: GitHub Issue 编号
        reviewer: 评审人名称
        approved: 是否通过
        comments: 评审意见
        owner: GitHub owner
        repo: GitHub repo name

    Returns:
        评审结果字典
    """
    result: dict[str, Any] = {
        "issue_number": issue_number,
        "reviewer": reviewer,
        "approved": approved,
        "comments": comments,
        "transition": None,
    }

    # 1. 尝试状态转移
    workflow = IssueWorkflow(issue_number, owner or "JXzfluser", repo or "OpsPulse")
    action = "approve" if approved else "reject"
    success = workflow.transition(action)
    result["transition"] = {
        "success": success,
        "from": "CREATED",
        "to": "REVIEW_PASS" if approved else "REVIEW_REJECT",
    }

    # 2. 生成评审 Comment
    status_icon = "✅" if approved else "❌"
    comment = f"""## OpsPulse 需求评审

| 字段 | 值 |
|------|-----|
| 评审人 | {reviewer} |
| 结果 | {status_icon} 通过 {'✅' if approved else '❌'} |
| 意见 | {comments} |
| 状态 | `{workflow.current()}` |

{workflow.history_summary() if workflow.history else ""}
"""

    # 3. 发布 Comment
    posted = False
    if owner and repo:
        try:
            comment_data = create_issue_comment(
                owner, repo, issue_number, comment
            )
            posted = True
            result["comment_url"] = comment_data.get("html_url")
        except Exception as e:
            result["comment_error"] = str(e)

    result["posted"] = posted
    return result
