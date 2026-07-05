"""parse_issue MCP tool and CLI."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import httpx

from opspulse_mcp.models.issue_spec import ParseIssueResult
from opspulse_mcp.parsers.frontmatter import extract_body, extract_frontmatter
from opspulse_mcp.parsers.label_mapper import apply_label_fallbacks
from opspulse_mcp.parsers.validation import validate_spec_dict


def parse_issue_markdown(
    markdown: str,
    labels: list[str] | None = None,
    schema: dict | None = None,
) -> ParseIssueResult:
    """Parse Issue markdown into spec, labels, errors, and ready flag."""
    labels = labels or []
    errors: list[str] = []
    raw_body = extract_body(markdown)

    spec, frontmatter_error = extract_frontmatter(markdown)
    if frontmatter_error:
        return ParseIssueResult(
            spec=None,
            raw_body=raw_body,
            labels=labels,
            errors=[frontmatter_error],
            ready=False,
        )

    assert spec is not None
    merged = apply_label_fallbacks(spec, labels)
    errors.extend(validate_spec_dict(merged, markdown=markdown, schema=schema))

    if not merged.get("acceptance"):
        errors.append("warning: acceptance is empty; agent should extract from body")

    issue_type = merged.get("type")
    if issue_type in ("feature", "bugfix") and not merged.get("affected_paths"):
        errors.append(
            "warning: affected_paths is empty; recommended for feature/bugfix issues"
        )

    blocking = [e for e in errors if not e.startswith("warning:")]
    ready = len(blocking) == 0

    return ParseIssueResult(
        spec=merged,
        raw_body=raw_body,
        labels=labels,
        errors=errors,
        ready=ready,
    )


def parse_issue_file(path: Path, labels: list[str] | None = None) -> ParseIssueResult:
    markdown = path.read_text(encoding="utf-8")
    return parse_issue_markdown(markdown, labels=labels)


def fetch_github_issue(owner: str, repo: str, issue_number: int) -> tuple[str, list[str]]:
    token = os.environ.get("GITHUB_PAT") or os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        payload = response.json()

    body = payload.get("body") or ""
    labels = [item["name"] for item in payload.get("labels", []) if "name" in item]
    return body, labels


def parse_issue(
    owner: str | None = None,
    repo: str | None = None,
    issue_number: int | None = None,
    file_path: str | Path | None = None,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    if file_path is not None:
        result = parse_issue_file(Path(file_path), labels=labels)
    elif owner and repo and issue_number is not None:
        markdown, gh_labels = fetch_github_issue(owner, repo, issue_number)
        merged_labels = labels if labels is not None else gh_labels
        result = parse_issue_markdown(markdown, labels=merged_labels)
    else:
        raise ValueError("Provide file_path or owner/repo/issue_number")

    return result.model_dump()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse OpsPulse Issue Spec from file or GitHub")
    parser.add_argument("--file", type=Path, help="Local Issue markdown file")
    parser.add_argument("--owner", help="GitHub repository owner")
    parser.add_argument("--repo", help="GitHub repository name")
    parser.add_argument("--issue-number", type=int, help="GitHub issue number")
    parser.add_argument(
        "--label",
        action="append",
        default=[],
        dest="labels",
        help="Additional label (repeatable)",
    )
    args = parser.parse_args(argv)

    try:
        if args.file:
            result = parse_issue(file_path=args.file, labels=args.labels or None)
        elif args.owner and args.repo and args.issue_number is not None:
            result = parse_issue(
                owner=args.owner,
                repo=args.repo,
                issue_number=args.issue_number,
                labels=args.labels or None,
            )
        else:
            parser.error("Provide --file or --owner --repo --issue-number")
            return 2
    except httpx.HTTPError as exc:
        print(json.dumps({"errors": [str(exc)], "ready": False}, indent=2))
        return 1
    except ValueError as exc:
        print(json.dumps({"errors": [str(exc)], "ready": False}, indent=2))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
