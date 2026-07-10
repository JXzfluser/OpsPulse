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


def create_branch(
    owner: str,
    repo: str,
    branch: str,
    from_ref: str = "main",
    *,
    token: str | None = None,
) -> dict[str, Any]:
    """Create a new branch from a ref using the Git_refs API."""
    url = f"{API_BASE}/repos/{owner}/{repo}/git/refs"
    with httpx.Client(timeout=30.0) as client:
        # Get SHA of source ref
        get_url = f"{API_BASE}/repos/{owner}/{repo}/git/ref/heads/{from_ref}"
        get_resp = client.get(get_url, headers=_headers(token))
        get_resp.raise_for_status()
        sha = get_resp.json()["object"]["sha"]

        # Create new branch
        payload = {"ref": f"refs/heads/{branch}", "sha": sha}
        resp = client.post(url, headers=_headers(token), json=payload)

    if resp.status_code == 201:
        return {"branch": branch, "sha": sha, "created": True}

    # Branch may already exist — try updating it
    if resp.status_code == 422:
        update_url = f"{API_BASE}/repos/{owner}/{repo}/git/refs/heads/{branch}"
        update_resp = client.patch(update_url, headers=_headers(token), json={"sha": sha, "force": True})
        if update_resp.status_code == 200:
            return {"branch": branch, "sha": sha, "created": False, "updated": True}
        raise GitHubError(
            f"create_branch failed: {update_resp.text}",
            status_code=update_resp.status_code,
        )

    raise GitHubError(
        f"create_branch failed ({resp.status_code}): {resp.text}",
        status_code=resp.status_code,
    )


def create_pull_request(
    owner: str,
    repo: str,
    title: str,
    body: str,
    head: str,
    base: str = "main",
    *,
    token: str | None = None,
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
) -> dict[str, Any]:
    """Create a PR and optionally add labels/assignees."""
    url = f"{API_BASE}/repos/{owner}/{repo}/pulls"
    payload = {"title": title, "body": body, "head": head, "base": base}

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, headers=_headers(token), json=payload)

    if resp.status_code != 201:
        raise GitHubError(
            f"create_pull_request failed ({resp.status_code}): {resp.text}",
            status_code=resp.status_code,
        )

    pr = resp.json()
    pr_number = pr["number"]

    # Add labels
    if labels:
        lbl_url = f"{API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/labels"
        lbl_resp = client.post(lbl_url, headers=_headers(token), json={"labels": labels})
        if lbl_resp.status_code not in (200, 201):
            # Non-fatal — warn but continue
            print(f"Warning: failed to add labels: {lbl_resp.text[:200]}")

    # Add assignees
    if assignees:
        asgn_url = f"{API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/assignees"
        asgn_resp = client.post(asgn_url, headers=_headers(token), json={"assignees": assignees})
        if asgn_resp.status_code not in (200, 201):
            print(f"Warning: failed to add assignees: {asgn_resp.text[:200]}")

    return {
        "pr_number": pr_number,
        "pr_url": pr["html_url"],
        "state": pr["state"],
        "title": pr["title"],
        "head": pr["head"]["ref"],
        "base": pr["base"]["ref"],
    }


def list_commits(
    owner: str,
    repo: str,
    head: str,
    *,
    token: str | None = None,
) -> list[dict[str, Any]]:
    """List commits in a branch."""
    url = f"{API_BASE}/repos/{owner}/{repo}/commits"
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=_headers(token), params={"head": f"{owner}:{head}", "per_page": 100})
        resp.raise_for_status()
        return resp.json()


def create_commit(
    owner: str,
    repo: str,
    branch: str,
    message: str,
    contents: list[dict[str, str]],
    *,
    token: str | None = None,
) -> dict[str, Any]:
    """
    Create a commit with file contents on a branch.
    contents: [{"path": "...", "content": "...", "sha": "..."}]
    sha is optional for new files.
    """
    # Get current tree SHA for the branch
    ref_url = f"{API_BASE}/repos/{owner}/{repo}/git/ref/heads/{branch}"
    with httpx.Client(timeout=30.0) as client:
        ref_resp = client.get(ref_url, headers=_headers(token))
        ref_resp.raise_for_status()
        commit_sha = ref_resp.json()["object"]["sha"]

        tree_resp = client.get(
            f"{API_BASE}/repos/{owner}/{repo}/git/commits/{commit_sha}",
            headers=_headers(token),
        )
        tree_resp.raise_for_status()
        tree_sha = tree_resp.json()["tree"]["sha"]

        # Build blob entries
        blob_entries = []
        for c in contents:
            blob_resp = client.post(
                f"{API_BASE}/repos/{owner}/{repo}/git/blobs",
                headers=_headers(token),
                json={"content": c["content"], "encoding": "utf-8"},
            )
            blob_resp.raise_for_status()
            blob_entries.append({
                "path": c["path"],
                "mode": "100644",
                "type": "blob",
                "sha": blob_resp.json()["sha"],
            })

        # Create new tree (incremental — keep existing blobs)
        tree_resp2 = client.post(
            f"{API_BASE}/repos/{owner}/{repo}/git/trees",
            headers=_headers(token),
            json={"base_tree": tree_sha, "tree": blob_entries},
        )
        tree_resp2.raise_for_status()
        new_tree_sha = tree_resp2.json()["sha"]

        # Create commit
        commit_resp = client.post(
            f"{API_BASE}/repos/{owner}/{repo}/git/commits",
            headers=_headers(token),
            json={
                "message": message,
                "tree": new_tree_sha,
                "parents": [commit_sha],
            },
        )
        commit_resp.raise_for_status()
        new_commit_sha = commit_resp.json()["sha"]

        # Update branch ref
        client.patch(
            f"{API_BASE}/repos/{owner}/{repo}/git/refs/heads/{branch}",
            headers=_headers(token),
            json={"sha": new_commit_sha, "force": True},
        )

    return {"commit_sha": new_commit_sha, "message": message, "branch": branch}
