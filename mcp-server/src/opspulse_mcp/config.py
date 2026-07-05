"""Load OpsPulse configuration from opspulse.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path(os.environ.get("OPS_PULSE_CONFIG", "./opspulse.yaml"))


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from start (or cwd) to locate repo root via opspulse.yaml or schemas/."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "opspulse.yaml").exists():
            return candidate
        if (candidate / "schemas" / "issue-spec.v1.json").exists():
            return candidate
    return current


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    path = (config_path or DEFAULT_CONFIG_PATH).resolve()
    if not path.exists():
        repo_root = find_repo_root(path.parent)
        fallback = repo_root / "opspulse.yaml"
        if fallback.exists():
            path = fallback
        else:
            return {"version": "1", "defaults": {}, "pipeline": {"default_mode": "local"}}
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def schema_path(repo_root: Path | None = None) -> Path:
    root = repo_root or find_repo_root()
    return root / "schemas" / "issue-spec.v1.json"


def local_runner_path(repo_root: Path | None = None) -> Path:
    root = repo_root or find_repo_root()
    return root / "internal" / "dev" / "local-runner" / "run-pipeline.sh"
