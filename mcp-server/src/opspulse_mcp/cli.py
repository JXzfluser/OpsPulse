"""opspulse CLI — 单命令入口：parse / trigger / status / init"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _load_env():
    """Load .env from repo root if present."""
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def cmd_parse(args):
    from opspulse_mcp.tools.parse_issue import parse_issue as _parse_issue
    result = _parse_issue(
        owner=args.owner,
        repo=args.repo,
        issue_number=args.issue_number,
        file_path=args.file,
        labels=args.labels or None,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ready") else 1


def cmd_trigger(args):
    from opspulse_mcp.tools.trigger_pipeline import trigger_pipeline as _trigger_pipeline
    result = _trigger_pipeline(
        args.pipeline_id,
        issue_file=args.issue_file,
        owner=args.owner,
        repo=args.repo,
        ref=args.ref,
        mode=args.mode,
        variables=args.var or None,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") in ("success", "partial") else 1


def cmd_status(args):
    from opspulse_mcp.tools.update_issue_status import update_issue_status as _update_issue_status
    acceptance_results = []
    for item in args.acceptance_result or []:
        if ":" not in item:
            print(f"Invalid --acceptance-result: {item}", file=sys.stderr)
            return 1
        ac_id, status = item.split(":", 1)
        acceptance_results.append({"id": ac_id, "passed": status.lower() == "passed"})

    spec = None
    if args.service or args.jdk_base_image:
        spec = {
            "service": {"name": args.service or "unknown"},
            "runtime": {"jdk_base_image": args.jdk_base_image or "unknown"},
            "acceptance": [
                {"id": r["id"], "given": "", "then": ""} for r in acceptance_results
            ],
        }

    result = _update_issue_status(
        args.state,
        pr_url=args.pr_url,
        pipeline_url=args.pipeline_url,
        acceptance_results=acceptance_results or None,
        spec=spec,
        owner=args.owner,
        repo=args.repo,
        issue_number=args.issue_number,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print(result["comment_body"])
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_init(args):
    from opspulse_mcp.tools.init_repo import init_repo as _init_repo
    result = _init_repo(
        args.repo_dir,
        args.owner,
        args.repo,
        github_pat=os.environ.get("GITHUB_PAT", ""),
        force=args.force,
    )
    if result["ok"]:
        print(f"✅ OpsPulse initialized in {args.repo_dir}")
        for f in result["files_created"]:
            print(f"   📄 {f}")
        return 0
    else:
        print(f"❌ {result['error']}", file=sys.stderr)
        return 1


def main():
    _load_env()

    parser = argparse.ArgumentParser(
        prog="opspulse",
        description="OpsPulse: Issue-to-Deploy glue layer for CI/CD",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # parse
    p_parse = subparsers.add_parser("parse", help="Parse Issue spec from GitHub or file")
    p_parse.add_argument("--file", type=Path, help="Local Issue markdown file")
    p_parse.add_argument("--owner", help="GitHub owner")
    p_parse.add_argument("--repo", help="GitHub repo name")
    p_parse.add_argument("--issue-number", type=int, help="GitHub issue number")
    p_parse.add_argument("--label", action="append", default=[], dest="labels")
    p_parse.set_defaults(func=cmd_parse)

    # trigger
    p_trigger = subparsers.add_parser("trigger", help="Trigger CI/CD pipeline")
    p_trigger.add_argument("pipeline_id", choices=["pr-validation", "deploy-dev", "deploy-staging"])
    p_trigger.add_argument("--issue-file", type=Path)
    p_trigger.add_argument("--owner")
    p_trigger.add_argument("--repo")
    p_trigger.add_argument("--ref")
    p_trigger.add_argument("--mode", choices=["local", "github-actions", "harness"])
    p_trigger.add_argument("--var", action="append", help="Variable KEY=VALUE")
    p_trigger.set_defaults(func=cmd_trigger)

    # status
    p_status = subparsers.add_parser("status", help="Update Issue status and post comment")
    p_status.add_argument("--state", required=True, choices=["parsed", "in-dev", "pr-open", "testing", "deployed", "failed"])
    p_status.add_argument("--pr-url")
    p_status.add_argument("--pipeline-url")
    p_status.add_argument("--dry-run", action="store_true")
    p_status.add_argument("--service")
    p_status.add_argument("--jdk-base-image")
    p_status.add_argument("--acceptance-result", action="append")
    p_status.add_argument("--owner")
    p_status.add_argument("--repo")
    p_status.add_argument("--issue-number", type=int)
    p_status.set_defaults(func=cmd_status)

    # init
    p_init = subparsers.add_parser("init", help="Initialize repo with OpsPulse config files")
    p_init.add_argument("repo_dir", nargs="?", default=".")
    p_init.add_argument("--owner", default="JXzfluser")
    p_init.add_argument("--repo", default="OpsPulse")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
