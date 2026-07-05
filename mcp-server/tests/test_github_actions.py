"""Tests for GitHub Actions dispatch resolution."""

from __future__ import annotations

import pytest

from opspulse_mcp.pipeline.github_actions import resolve_github_actions_dispatch


def test_resolve_from_issue_spec_and_config():
    spec = {
        "service": {"name": "chuanplus-platform-gateway"},
        "repository": {"owner": "JXzfluser", "name": "chuanplus-platform"},
        "ci": {"inputs": {"env": "test"}},
    }
    config = {
        "pipeline": {
            "github_actions": {
                "ref": "main",
                "repositories": {
                    "JXzfluser/chuanplus-platform": {
                        "workflow": "cicd.yml",
                        "service_input": "module",
                        "pipelines": {
                            "pr-validation": {"inputs": {"env": "test"}},
                        },
                    }
                },
            }
        }
    }

    result = resolve_github_actions_dispatch("pr-validation", spec=spec, config=config)

    assert result["owner"] == "JXzfluser"
    assert result["repo"] == "chuanplus-platform"
    assert result["workflow"] == "cicd.yml"
    assert result["inputs"]["module"] == "chuanplus-platform-gateway"
    assert result["inputs"]["env"] == "test"


def test_resolve_requires_owner_repo():
    with pytest.raises(ValueError, match="owner/repo"):
        resolve_github_actions_dispatch("pr-validation", spec={}, config={})
