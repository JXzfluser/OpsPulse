"""Tests for trigger_pipeline tool."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from opspulse_mcp.tools.trigger_pipeline import parse_stage_results, trigger_pipeline

SAMPLE_OUTPUT = """
OpsPulse local-runner
OPS_STAGE:validate_spec:success:schema valid
OPS_STAGE:jdk_base_verify:skipped:docker not available
OPS_STAGE:microservice_build:success:fixture artifact ready
OPS_STAGE:service_image_build:skipped:docker not available
OPS_STAGE:smoke_test:success:smoke checks passed
"""


def test_parse_stage_results():
    stages = parse_stage_results(SAMPLE_OUTPUT)
    assert len(stages) == 5
    assert stages[0] == {"name": "validate_spec", "status": "success", "message": "schema valid"}
    assert stages[1]["status"] == "skipped"


@patch("opspulse_mcp.tools.trigger_pipeline.subprocess.run")
def test_trigger_pipeline_local_success(mock_run: MagicMock, tmp_path: Path):
    repo_root = tmp_path
    runner_dir = repo_root / "local-runner"
    runner_dir.mkdir()
    runner = runner_dir / "run-pipeline.sh"
    runner.write_text("#!/bin/bash\necho OPS_STAGE:test:success:ok\n", encoding="utf-8")
    runner.chmod(0o755)
    (repo_root / "opspulse.yaml").write_text("version: '1'\n", encoding="utf-8")

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="OPS_STAGE:validate_spec:success:ok\n",
        stderr="",
    )

    with patch("opspulse_mcp.tools.trigger_pipeline.find_repo_root", return_value=repo_root):
        with patch("opspulse_mcp.tools.trigger_pipeline.local_runner_path", return_value=runner):
            result = trigger_pipeline("pr-validation", issue_file="issue.md", repo_root=repo_root)

    assert result["status"] == "success"
    assert result["stage_results"][0]["name"] == "validate_spec"
    mock_run.assert_called_once()


@patch("opspulse_mcp.tools.trigger_pipeline.subprocess.run")
def test_trigger_pipeline_failure_exit_code(mock_run: MagicMock, tmp_path: Path):
    repo_root = tmp_path
    runner = repo_root / "local-runner" / "run-pipeline.sh"
    runner.parent.mkdir()
    runner.write_text("#!/bin/bash\n", encoding="utf-8")
    runner.chmod(0o755)

    mock_run.return_value = MagicMock(
        returncode=1,
        stdout="OPS_STAGE:validate_spec:failed:bad spec\n",
        stderr="",
    )

    with patch("opspulse_mcp.tools.trigger_pipeline.find_repo_root", return_value=repo_root):
        with patch("opspulse_mcp.tools.trigger_pipeline.local_runner_path", return_value=runner):
            result = trigger_pipeline("pr-validation", repo_root=repo_root)

    assert result["status"] == "failed"
    assert result["stage_results"][0]["status"] == "failed"
