"""Tests for trigger_pipeline github-actions mode."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from opspulse_mcp.tools.trigger_pipeline import trigger_pipeline


@patch("opspulse_mcp.tools.trigger_pipeline.dispatch_workflow")
def test_trigger_pipeline_github_actions(mock_dispatch: MagicMock, tmp_path: Path):
    repo_root = tmp_path
    (repo_root / "opspulse.yaml").write_text(
        """
version: "1"
pipeline:
  default_mode: github-actions
  github_actions:
    repositories:
      acme/demo:
        workflow: ci.yml
        service_input: module
""",
        encoding="utf-8",
    )

    mock_dispatch.return_value = {
        "dispatched": True,
        "actions_url": "https://github.com/acme/demo/actions",
    }

    spec = {
        "service": {"name": "order-svc"},
        "repository": {"owner": "acme", "name": "demo"},
    }

    with patch("opspulse_mcp.tools.trigger_pipeline.find_repo_root", return_value=repo_root):
        result = trigger_pipeline(
            "pr-validation",
            owner="acme",
            repo="demo",
            spec=spec,
            repo_root=repo_root,
        )

    assert result["status"] == "success"
    assert result["mode"] == "github-actions"
    assert result["logs_url"] == "https://github.com/acme/demo/actions"
    mock_dispatch.assert_called_once()
