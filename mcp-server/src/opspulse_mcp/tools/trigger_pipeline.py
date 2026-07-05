"""trigger_pipeline MCP tool and CLI."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import uuid
from pathlib import Path
from typing import Any

from opspulse_mcp.config import find_repo_root, load_config, local_runner_path
from opspulse_mcp.github.client import GitHubError, dispatch_workflow
from opspulse_mcp.models.issue_spec import PipelineId, PipelineMode
from opspulse_mcp.pipeline.github_actions import resolve_github_actions_dispatch
from opspulse_mcp.tools.parse_issue import parse_issue_file

STAGE_LINE_RE = re.compile(r"^OPS_STAGE:([^:]+):([^:]+)(?::(.*))?$")


def parse_stage_results(output: str) -> list[dict[str, str]]:
    stages: list[dict[str, str]] = []
    for line in output.splitlines():
        match = STAGE_LINE_RE.match(line.strip())
        if not match:
            continue
        name, status, message = match.group(1), match.group(2), match.group(3) or ""
        stages.append({"name": name, "status": status, "message": message})
    return stages


def overall_status(stage_results: list[dict[str, str]]) -> str:
    if not stage_results:
        return "unknown"
    statuses = {item["status"] for item in stage_results}
    if "failed" in statuses:
        return "failed"
    if statuses <= {"success", "skipped"}:
        return "success"
    return "partial"


def _load_spec_from_issue_file(issue_file: str | Path | None) -> dict[str, Any] | None:
    if not issue_file:
        return None
    result = parse_issue_file(Path(issue_file))
    return result.spec


def _trigger_local(
    pipeline_id: PipelineId,
    *,
    issue_file: str | Path | None,
    variables: dict[str, str] | None,
    repo_root: Path,
) -> dict[str, Any]:
    runner = local_runner_path(repo_root)
    if not runner.exists():
        raise FileNotFoundError(f"local-runner not found: {runner}")

    cmd = [str(runner), pipeline_id]
    if issue_file:
        cmd.extend(["--issue-file", str(issue_file)])

    env = os.environ.copy()
    env.update(variables or {})
    config = load_config(repo_root / "opspulse.yaml")
    defaults = config.get("defaults", {})
    runtime = defaults.get("runtime", {})
    if jdk := runtime.get("jdk_base_image"):
        env.setdefault("JDK_BASE_IMAGE", str(jdk))

    completed = subprocess.run(
        cmd,
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    combined = completed.stdout + ("\n" + completed.stderr if completed.stderr else "")
    stage_results = parse_stage_results(combined)
    status = "failed" if completed.returncode != 0 else overall_status(stage_results)

    return {
        "execution_id": str(uuid.uuid4()),
        "status": status,
        "mode": "local",
        "stage_results": stage_results,
        "logs_url": None,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "exit_code": completed.returncode,
    }


def _trigger_github_actions(
    pipeline_id: PipelineId,
    *,
    owner: str | None,
    repo: str | None,
    ref: str | None,
    issue_file: str | Path | None,
    spec: dict[str, Any] | None,
    variables: dict[str, str] | None,
    repo_root: Path,
) -> dict[str, Any]:
    config = load_config(repo_root / "opspulse.yaml")
    if spec is None and issue_file:
        parsed = parse_issue_file(Path(issue_file))
        spec = parsed.spec

    dispatch = resolve_github_actions_dispatch(
        pipeline_id,
        spec=spec,
        config=config,
        owner=owner,
        repo=repo,
        ref=ref,
        variables=variables,
    )

    result = dispatch_workflow(
        dispatch["owner"],
        dispatch["repo"],
        dispatch["workflow"],
        ref=dispatch["ref"],
        inputs=dispatch["inputs"],
    )

    return {
        "execution_id": str(uuid.uuid4()),
        "status": "success",
        "mode": "github-actions",
        "stage_results": [
            {
                "name": "workflow_dispatch",
                "status": "success",
                "message": f"{dispatch['workflow']} @ {dispatch['ref']}",
            }
        ],
        "logs_url": result["actions_url"],
        "dispatch": result,
        "inputs": dispatch["inputs"],
    }


def trigger_pipeline(
    pipeline_id: PipelineId,
    *,
    issue_file: str | Path | None = None,
    owner: str | None = None,
    repo: str | None = None,
    ref: str | None = None,
    mode: PipelineMode | None = None,
    variables: dict[str, str] | None = None,
    spec: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or find_repo_root()
    config = load_config(root / "opspulse.yaml")
    pipeline_cfg = config.get("pipeline") or {}
    resolved_mode: PipelineMode = mode or pipeline_cfg.get("default_mode", "local")  # type: ignore[assignment]

    if resolved_mode == "harness":
        return {
            "execution_id": str(uuid.uuid4()),
            "status": "failed",
            "mode": "harness",
            "stage_results": [],
            "logs_url": None,
            "errors": ["Mode 'harness' is not implemented yet; use github-actions or local"],
        }

    try:
        if resolved_mode == "github-actions":
            return _trigger_github_actions(
                pipeline_id,
                owner=owner,
                repo=repo,
                ref=ref,
                issue_file=issue_file,
                spec=spec,
                variables=variables,
                repo_root=root,
            )
        return _trigger_local(
            pipeline_id,
            issue_file=issue_file,
            variables=variables,
            repo_root=root,
        )
    except (GitHubError, ValueError) as exc:
        return {
            "execution_id": str(uuid.uuid4()),
            "status": "failed",
            "mode": resolved_mode,
            "stage_results": [
                {"name": "trigger", "status": "failed", "message": str(exc)},
            ],
            "logs_url": None,
            "errors": [str(exc)],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trigger OpsPulse pipeline")
    parser.add_argument("pipeline_id", choices=["pr-validation", "deploy-dev", "deploy-staging"])
    parser.add_argument("--issue-file", type=Path)
    parser.add_argument("--owner")
    parser.add_argument("--repo")
    parser.add_argument("--ref")
    parser.add_argument("--mode", choices=["local", "harness", "github-actions"])
    args = parser.parse_args(argv)

    try:
        result = trigger_pipeline(
            args.pipeline_id,  # type: ignore[arg-type]
            issue_file=args.issue_file,
            owner=args.owner,
            repo=args.repo,
            ref=args.ref,
            mode=args.mode,  # type: ignore[arg-type]
        )
    except FileNotFoundError as exc:
        print(json.dumps({"status": "failed", "errors": [str(exc)]}, indent=2))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in ("success", "partial") else 1


if __name__ == "__main__":
    raise SystemExit(main())
