"""创建 PR Tool — 完整功能：分支管理 + PR 描述生成 + 代码提交"""
from __future__ import annotations

import json
import re
from typing import Any

from opspulse_mcp.github.client import (
    create_branch,
    create_commit,
    create_pull_request,
)
from opspulse_mcp.workflow import IssueWorkflow

BRANCH_PREFIX = "opspulse/"


def _slugify(text: str, max_len: int = 40) -> str:
    """Convert text to a git-safe branch slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text[:max_len] or "update"


def _generate_pr_title(issue_title: str, service: str, issue_number: int) -> str:
    """Generate conventional commit-style PR title."""
    slug = _slugify(issue_title, max_len=30)
    return f"feat({service}): {slug} (#{issue_number})"


def _generate_pr_body(
    issue_number: int,
    issue_title: str,
    spec: dict,
    breakdown: list[dict] | None = None,
    design_summary: str | None = None,
) -> str:
    """Generate a comprehensive PR description template."""
    service = spec.get("service", {}).get("name", "unknown")
    issue_type = spec.get("type", "feature")
    acceptance = spec.get("acceptance", [])

    body = f"""## Summary

Closes #{issue_number}

### Description
{issue_title}

---

## Service: `{service}`
- **Type**: {issue_type}
- **Scope**: {spec.get('scope', 'N/A')}
- **Priority**: {spec.get('priority', 'N/A')}

---

## Changes

<!-- Describe what files were modified and why -->
- [ ] Service code updates
- [ ] Test coverage added
- [ ] Configuration changes
- [ ] Documentation updated

---
"""

    if design_summary:
        body += f"""## Design Notes

{design_summary}

---
"""

    if breakdown:
        body += "## Tasks\n\n"
        for i, task in enumerate(breakdown, 1):
            status = "x" if task.get("done") else " "
            body += f"- [ ] {i}. {task.get('title', 'Task')}\n"
        body += "\n---\n"

    if acceptance:
        body += "## Acceptance Criteria\n\n"
        for ac in acceptance:
            status = "x" if ac.get("passed") else " "
            body += f"- [ ] **{ac.get('id', '?')}**: {ac.get('then', 'Check expected outcome')}\n"
        body += "\n---\n"

    body += f"""## How to Test

```bash
# Build
make build || mvn clean package

# Run tests
make test || mvn test

# Deploy to dev
make deploy-dev || ./scripts/deploy.sh dev
```

---

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes
"""
    return body


def ops_create_pr(
    issue_number: int,
    owner: str,
    repo: str,
    branch: str | None = None,
    title: str | None = None,
    body: str | None = None,
    spec: dict | None = None,
    breakdown: list[dict] | None = None,
    design_summary: str | None = None,
    commit_contents: list[dict] | None = None,
) -> dict[str, Any]:
    """自动创建 PR 并关联 Issue。

    Args:
        issue_number: 关联的 Issue 编号
        owner: GitHub owner
        repo: GitHub repo name
        branch: 分支名（可选，自动生成 opspulse/{issue_number}-{slug}）
        title: PR 标题（可选，自动生成）
        body: PR 描述（可选，自动生成）
        spec: Issue Spec 字典（用于生成 PR 描述）
        breakdown: 任务拆分列表（用于生成 PR 描述）
        design_summary: 设计方案摘要（用于生成 PR 描述）
        commit_contents: 文件内容列表 [{path, content}]（可选，自动提交代码到分支）

    Returns:
        PR URL 和状态转移结果
    """
    if not spec:
        spec = {}

    service = spec.get("service", {}).get("name", "service")
    issue_title = spec.get("_issue_title", f"Issue #{issue_number}")

    # 1. 自动生成分支名
    if not branch:
        slug = _slugify(issue_title, max_len=30)
        branch = f"{BRANCH_PREFIX}{issue_number}-{slug}"

    # 2. 自动创建/更新分支
    try:
        branch_result = create_branch(owner, repo, branch, from_ref="main")
    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to create branch '{branch}': {exc}",
            "branch": branch,
        }

    # 3. 如果有代码内容，自动提交到分支
    commit_shas = []
    if commit_contents:
        try:
            commit_msg = f"feat({service}): {issue_title} (#{issue_number})"
            commit_result = create_commit(owner, repo, branch, commit_msg, commit_contents)
            commit_shas.append(commit_result["commit_sha"])
        except Exception as exc:
            return {
                "success": False,
                "error": f"Failed to commit code: {exc}",
                "branch": branch,
                "commits": commit_shas,
            }

    # 4. 自动生成 PR 标题和描述
    if not title:
        title = _generate_pr_title(issue_title, service, issue_number)

    if not body:
        body = _generate_pr_body(
            issue_number, issue_title, spec,
            breakdown=breakdown,
            design_summary=design_summary,
        )

    # 5. 创建 PR
    try:
        pr_result = create_pull_request(
            owner=owner,
            repo=repo,
            title=title,
            body=body,
            head=branch,
            base="main",
            labels=["opspulse", f"type:{spec.get('type', 'feature')}"],
            assignees=[],
        )
    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to create PR: {exc}",
            "branch": branch,
            "commits": commit_shas,
        }

    # 6. 状态转移
    workflow = IssueWorkflow(issue_number, owner, repo)
    success = workflow.transition("create_pr")

    return {
        "success": True,
        "pr_number": pr_result["pr_number"],
        "pr_url": pr_result["pr_url"],
        "branch": branch,
        "commits": commit_shas,
        "transition": {"success": success, "from": "CODING_DONE", "to": "PR_CREATED"},
        "workflow": workflow.history_summary(),
    }