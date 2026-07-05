"""update_issue_status MCP tool and CLI."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from opspulse_mcp.github.client import GitHubError, create_issue_comment
from opspulse_mcp.models.issue_spec import IssueState

VALID_STATES: set[str] = {
    "parsed",
    "in-dev",
    "pr-open",
    "testing",
    "deployed",
    "failed",
}


def render_acceptance_checklist(
    acceptance: list[dict[str, Any]] | None,
    acceptance_results: list[dict[str, Any]] | None,
) -> str:
    results_by_id = {
        item["id"]: item.get("passed", False)
        for item in (acceptance_results or [])
        if "id" in item
    }
    lines: list[str] = []
    for item in acceptance or []:
        ac_id = item.get("id", "?")
        passed = results_by_id.get(ac_id, False)
        checkbox = "x" if passed else " "
        summary = item.get("then") or item.get("given") or ""
        lines.append(f"- [{checkbox}] {ac_id}: {summary}")
    if not lines:
        lines.append("- [ ] (no acceptance criteria recorded)")
    return "\n".join(lines)


def build_status_comment(
    state: IssueState,
    *,
    service_name: str | None = None,
    jdk_base_image: str | None = None,
    pr_url: str | None = None,
    pipeline_url: str | None = None,
    acceptance: list[dict[str, Any]] | None = None,
    acceptance_results: list[dict[str, Any]] | None = None,
    error_message: str | None = None,
) -> str:
    if state not in VALID_STATES:
        raise ValueError(f"Invalid state '{state}'; expected one of {sorted(VALID_STATES)}")

    lines = [
        "## OpsPulse Delivery Status",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| State | `{state}` |",
    ]

    if service_name:
        lines.append(f"| Service | {service_name} |")
    if jdk_base_image:
        lines.append(f"| JDK Base Image | `{jdk_base_image}` |")
    if pr_url:
        lines.append(f"| PR | {pr_url} |")
    if pipeline_url:
        lines.append(f"| Pipeline | {pipeline_url} |")

    lines.extend(["", "### Acceptance", render_acceptance_checklist(acceptance, acceptance_results)])

    if error_message:
        lines.extend(["", "### Error", f"> {error_message}"])

    return "\n".join(lines)


def update_issue_status(
    state: IssueState,
    *,
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
    service_name = None
    jdk_base_image = None
    acceptance = None
    if spec:
        service = spec.get("service") or {}
        runtime = spec.get("runtime") or {}
        service_name = service.get("name")
        jdk_base_image = runtime.get("jdk_base_image")
        acceptance = spec.get("acceptance")
        repository = spec.get("repository") or {}
        owner = owner or repository.get("owner")
        repo = repo or repository.get("name")

    comment_body = build_status_comment(
        state,
        service_name=service_name,
        jdk_base_image=jdk_base_image,
        pr_url=pr_url,
        pipeline_url=pipeline_url,
        acceptance=acceptance,
        acceptance_results=acceptance_results,
        error_message=error_message,
    )

    result: dict[str, Any] = {"state": state, "comment_body": comment_body}

    if dry_run or not (owner and repo and issue_number is not None):
        result["posted"] = False
        return result

    try:
        comment = create_issue_comment(owner, repo, issue_number, comment_body)
        result["posted"] = True
        result["comment_url"] = comment.get("html_url")
        result["comment_id"] = comment.get("id")
    except GitHubError as exc:
        result["posted"] = False
        result["errors"] = [str(exc)]

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate OpsPulse Issue status comment")
    parser.add_argument("--state", required=True, choices=sorted(VALID_STATES))
    parser.add_argument("--pr-url")
    parser.add_argument("--pipeline-url")
    parser.add_argument("--dry-run", action="store_true", help="Print comment without posting")
    parser.add_argument("--service", help="Override service name in comment")
    parser.add_argument("--jdk-base-image", help="Override JDK base image in comment")
    parser.add_argument(
        "--acceptance-result",
        action="append",
        default=[],
        metavar="ID:passed|failed",
        help="Acceptance result, e.g. AC-1:passed",
    )
    parser.add_argument("--owner", help="GitHub owner for posting comment")
    parser.add_argument("--repo", help="GitHub repo for posting comment")
    parser.add_argument("--issue-number", type=int, help="GitHub issue number for posting comment")
    args = parser.parse_args(argv)

    acceptance_results: list[dict[str, Any]] = []
    for item in args.acceptance_result:
        if ":" not in item:
            print(f"Invalid --acceptance-result: {item}", file=sys.stderr)
            return 1
        ac_id, status = item.split(":", 1)
        acceptance_results.append({"id": ac_id, "passed": status.lower() == "passed"})

    spec: dict[str, Any] | None = None
    if args.service or args.jdk_base_image:
        spec = {
            "service": {"name": args.service or "unknown"},
            "runtime": {"jdk_base_image": args.jdk_base_image or "unknown"},
            "acceptance": [{"id": r["id"], "given": "", "then": ""} for r in acceptance_results],
        }

    result = update_issue_status(
        args.state,  # type: ignore[arg-type]
        pr_url=args.pr_url,
        pipeline_url=args.pipeline_url,
        acceptance_results=acceptance_results or None,
        spec=spec,
        owner=args.owner,
        repo=args.repo,
        issue_number=args.issue_number,
        dry_run=args.dry_run,
    )

    if args.dry_run or not result.get("posted"):
        if args.dry_run:
            print(result["comment_body"])
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
