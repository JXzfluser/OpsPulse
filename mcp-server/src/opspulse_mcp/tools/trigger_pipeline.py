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
from opspulse_mcp.models.issue_spec import PipelineId, PipelineMode

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


def trigger_pipeline(
    pipeline_id: PipelineId,
    *,
    issue_file: str | Path | None = None,
    ref: str | None = None,
    mode: PipelineMode = "local",
    variables: dict[str, str] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    if mode != "local":
        return {
            "execution_id": str(uuid.uuid4()),
            "status": "failed",
            "stage_results": [],
            "logs_url": None,
            "errors": [f"Mode '{mode}' is not implemented in MVP; use mode=local"],
        }

    root = repo_root or find_repo_root()
    runner = local_runner_path(root)
    if not runner.exists():
        raise FileNotFoundError(f"local-runner not found: {runner}")

    cmd = [str(runner), pipeline_id]
    if issue_file:
        cmd.extend(["--issue-file", str(issue_file)])

    env = os.environ.copy()
    env.update(variables or {})
    config = load_config(root / "opspulse.yaml")
    defaults = config.get("defaults", {})
    runtime = defaults.get("runtime", {})
    if jdk := runtime.get("jdk_base_image"):
        env.setdefault("JDK_BASE_IMAGE", str(jdk))

    completed = subprocess.run(
        cmd,
        cwd=root,
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
        "stage_results": stage_results,
        "logs_url": None,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "exit_code": completed.returncode,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trigger OpsPulse pipeline via local-runner")
    parser.add_argument("pipeline_id", choices=["pr-validation", "deploy-dev", "deploy-staging"])
    parser.add_argument("--issue-file", type=Path)
    parser.add_argument("--ref")
    parser.add_argument("--mode", default="local", choices=["local", "harness", "github-actions"])
    args = parser.parse_args(argv)

    try:
        result = trigger_pipeline(
            args.pipeline_id,  # type: ignore[arg-type]
            issue_file=args.issue_file,
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
