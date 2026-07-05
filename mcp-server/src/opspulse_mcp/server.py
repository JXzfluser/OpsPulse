"""FastMCP server entrypoint."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from opspulse_mcp.tools.parse_issue import parse_issue as _parse_issue
from opspulse_mcp.tools.trigger_pipeline import trigger_pipeline as _trigger_pipeline
from opspulse_mcp.tools.update_issue_status import update_issue_status as _update_issue_status

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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
