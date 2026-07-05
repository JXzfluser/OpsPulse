"""FastMCP server entrypoint."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opspulse_mcp.tools.parse_issue import parse_issue as _parse_issue
from opspulse_mcp.tools.trigger_pipeline import trigger_pipeline as _trigger_pipeline
from opspulse_mcp.tools.update_issue_status import update_issue_status as _update_issue_status
from opspulse_mcp.tools.init_repo import init_repo as _init_repo
from opspulse_mcp.tools.ops_review import ops_review as _ops_review
from opspulse_mcp.tools.ops_design import ops_design as _ops_design
from opspulse_mcp.tools.ops_breakdown import ops_breakdown as _ops_breakdown
from opspulse_mcp.tools.ops_create_pr import ops_create_pr as _ops_create_pr
from opspulse_mcp.tools.ops_smoke_test import ops_smoke_test as _ops_smoke_test
from opspulse_mcp.tools.ops_deploy import ops_deploy as _ops_deploy

mcp = FastMCP("opspulse")


@mcp.tool()
def parse_issue(
    owner: str | None = None,
    repo: str | None = None,
    issue_number: int | None = None,
    file_path: str | None = None,
) -> dict[str, Any]:
    """Parse GitHub Issue or local markdown into Issue Spec with ready gate."""
    return _parse_issue(
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        file_path=file_path,
    )


@mcp.tool()
def trigger_pipeline(
    pipeline_id: str,
    issue_file: str | None = None,
    owner: str | None = None,
    repo: str | None = None,
    ref: str | None = None,
    mode: str | None = None,
    variables: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Trigger pr-validation or deploy-dev via GitHub Actions or local dev runner."""
    return _trigger_pipeline(
        pipeline_id,  # type: ignore[arg-type]
        issue_file=issue_file,
        owner=owner,
        repo=repo,
        ref=ref,
        mode=mode,  # type: ignore[arg-type]
        variables=variables,
    )


@mcp.tool()
def update_issue_status(
    state: str,
    pr_url: str | None = None,
    pipeline_url: str | None = None,
    acceptance_results: list[dict[str, Any]] | None = None,
    spec: dict[str, Any] | None = None,
    error_message: str | None = None,
    owner: str | None = None,
    repo: str | None = None,
    issue_number: int | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Generate and optionally post structured Markdown comment on GitHub Issue."""
    return _update_issue_status(
        state,  # type: ignore[arg-type]
        pr_url=pr_url,
        pipeline_url=pipeline_url,
        acceptance_results=acceptance_results,
        spec=spec,
        error_message=error_message,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        dry_run=dry_run,
    )


@mcp.tool()
def init_opsulse_repo(
    repo_dir: str,
    owner: str | None = None,
    repo: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Initialize a repository with OpsPulse config files (opspulse.yaml, workflows, issue templates)."""
    return _init_repo(repo_dir, owner or "JXzfluser", repo or "OpsPulse", force=force)


@mcp.tool()
def ops_review(
    issue_number: int,
    reviewer: str,
    approved: bool,
    comments: str,
    owner: str | None = None,
    repo: str | None = None,
) -> dict[str, Any]:
    """需求评审：检查 Issue 完整性并给出评审意见。"""
    return _ops_review(
        issue_number=issue_number,
        reviewer=reviewer,
        approved=approved,
        comments=comments,
        owner=owner,
        repo=repo,
    )


@mcp.tool()
def ops_design(
    issue_number: int,
    issue_spec: dict[str, Any],
    owner: str | None = None,
    repo: str | None = None,
) -> dict[str, Any]:
    """根据 Issue Spec 自动生成技术方案。"""
    return _ops_design(
        issue_number=issue_number,
        issue_spec=issue_spec,
        owner=owner,
        repo=repo,
    )


@mcp.tool()
def ops_breakdown(
    issue_number: int,
    issue_spec: dict[str, Any],
    design_doc: str,
    owner: str | None = None,
    repo: str | None = None,
) -> dict[str, Any]:
    """将 Issue 拆分为可执行的任务列表。"""
    return _ops_breakdown(
        issue_number=issue_number,
        issue_spec=issue_spec,
        design_doc=design_doc,
        owner=owner,
        repo=repo,
    )


@mcp.tool()
def ops_create_pr(
    issue_number: int,
    branch: str,
    title: str,
    body: str,
    owner: str,
    repo: str,
) -> dict[str, Any]:
    """自动创建 PR 并关联 Issue。"""
    return _ops_create_pr(
        issue_number=issue_number,
        branch=branch,
        title=title,
        body=body,
        owner=owner,
        repo=repo,
    )


@mcp.tool()
def ops_smoke_test(
    issue_number: int,
    pipeline_id: str,
    owner: str,
    repo: str,
) -> dict[str, Any]:
    """冒烟测试：部署到 staging 并验证 acceptance criteria。"""
    return _ops_smoke_test(
        issue_number=issue_number,
        pipeline_id=pipeline_id,
        owner=owner,
        repo=repo,
    )


@mcp.tool()
def ops_deploy(
    issue_number: int,
    environment: str,
    percentage: int = 100,
    owner: str | None = None,
    repo: str | None = None,
) -> dict[str, Any]:
    """灰度/全量部署，支持自动回滚。"""
    return _ops_deploy(
        issue_number=issue_number,
        environment=environment,
        percentage=percentage,
        owner=owner,
        repo=repo,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
