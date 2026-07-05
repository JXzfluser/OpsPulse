"""创建 PR Tool — 编码完成后自动创建 PR"""
from __future__ import annotations

import json
from typing import Any

import httpx

from opspulse_mcp.workflow import IssueWorkflow


def ops_create_pr(
    issue_number: int,
    branch: str,
    title: str,
    body: str,
    owner: str,
    repo: str,
) -> dict[str, Any]:
    """自动创建 PR 并关联 Issue。

    Args:
        issue_number: 关联的 Issue 编号
        branch: PR 目标分支
        title: PR 标题
        body: PR 描述
        owner: GitHub owner
        repo: GitHub repo name

    Returns:
        PR URL 和状态转移结果
    """
    token = __import__("os").environ.get("GITHUB_PAT", "")
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    # 1. 创建 PR
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = {
        "title": title,
        "body": body,
        "head": branch,
        "base": "main",
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, headers=headers, json=payload)

    if resp.status_code != 201:
        return {
            "success": False,
            "error": f"GitHub API returned {resp.status_code}: {resp.text[:500]}",
        }

    pr = resp.json()
    pr_url = pr.get("html_url", "")

    # 2. 状态转移
    workflow = IssueWorkflow(issue_number, owner, repo)
    success = workflow.transition("create_pr")

    return {
        "success": True,
        "pr_url": pr_url,
        "pr_number": pr.get("number"),
        "transition": {"success": success, "from": "CODING_DONE", "to": "PR_CREATED"},
        "workflow": workflow.history_summary(),
    }
