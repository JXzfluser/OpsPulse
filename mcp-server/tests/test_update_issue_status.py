"""Tests for update_issue_status tool."""

from __future__ import annotations

import pytest

from opspulse_mcp.tools.update_issue_status import build_status_comment, update_issue_status

SAMPLE_SPEC = {
    "service": {"name": "order-service"},
    "runtime": {"jdk_base_image": "registry.example.com/platform/jdk8-base:1.0"},
    "acceptance": [
        {"id": "AC-1", "given": "service running", "then": "health UP"},
        {"id": "AC-2", "given": "API deployed", "then": "POST returns 201"},
    ],
}


def test_deployed_comment_renders_acceptance_checkboxes():
    result = update_issue_status(
        "deployed",
        spec=SAMPLE_SPEC,
        acceptance_results=[
            {"id": "AC-1", "passed": True},
            {"id": "AC-2", "passed": False},
        ],
        pr_url="https://github.com/org/repo/pull/1",
    )
    body = result["comment_body"]
    assert "## OpsPulse Delivery Status" in body
    assert "| State | `deployed` |" in body
    assert "| Service | order-service |" in body
    assert "- [x] AC-1: health UP" in body
    assert "- [ ] AC-2: POST returns 201" in body
    assert "https://github.com/org/repo/pull/1" in body


@pytest.mark.parametrize("state", ["parsed", "in-dev", "pr-open", "testing", "deployed", "failed"])
def test_all_valid_states(state):
    body = build_status_comment(state)  # type: ignore[arg-type]
    assert f"| State | `{state}` |" in body


def test_invalid_state_raises():
    with pytest.raises(ValueError, match="Invalid state"):
        build_status_comment("unknown")  # type: ignore[arg-type]
