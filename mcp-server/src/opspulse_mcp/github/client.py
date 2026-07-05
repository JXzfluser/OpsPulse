"""GitHub API client for OpsPulse glue layer."""

from __future__ import annotations

import os
from typing import Any

import httpx

API_BASE = "https://api.github.com"


class GitHubError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def get_token() -> str:
    token = os.environ.get("GITHUB_PAT") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise GitHubError(
            "GITHUB_PAT or GITHUB_TOKEN is required for GitHub API calls"
        )
    return token


def _headers(token: str | None = None) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token or get_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def dispatch_workflow(
    owner: str,
    repo: str,
    workflow: str,
    *,
    ref: str = "main",
    inputs: dict[str, str] | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    """Trigger workflow_dispatch. workflow may be file name (cicd.yml) or numeric id."""
    url = f"{API_BASE}/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches"
    payload: dict[str, Any] = {"ref": ref}
    if inputs:
        payload["inputs"] = inputs

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=_headers(token), json=payload)

    if response.status_code == 204:
        return {
            "dispatched": True,
            "owner": owner,
            "repo": repo,
            "workflow": workflow,
            "ref": ref,
            "inputs": inputs or {},
            "actions_url": f"https://github.com/{owner}/{repo}/actions",
        }

    raise GitHubError(
        f"workflow_dispatch failed ({response.status_code}): {response.text}",
        status_code=response.status_code,
    )


def create_issue_comment(
    owner: str,
    repo: str,
    issue_number: int,
    body: str,
    *,
    token: str | None = None,
) -> dict[str, Any]:
    url = f"{API_BASE}/repos/{owner}/{repo}/issues/{issue_number}/comments"
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=_headers(token), json={"body": body})

    if response.status_code == 201:
        return response.json()

    raise GitHubError(
        f"create issue comment failed ({response.status_code}): {response.text}",
        status_code=response.status_code,
    )
