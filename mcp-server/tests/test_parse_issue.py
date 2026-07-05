"""Tests for parse_issue tool."""

from __future__ import annotations

from pathlib import Path

import pytest

from opspulse_mcp.parsers.label_mapper import apply_label_fallbacks
from opspulse_mcp.parsers.validation import load_schema
from opspulse_mcp.tools.parse_issue import parse_issue_file, parse_issue_markdown

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = REPO_ROOT / "examples" / "issues"
SCHEMA = load_schema()


@pytest.mark.parametrize(
    "filename,expected_service,expected_ready",
    [
        ("001-order-service-feature.md", "order-service", True),
        ("002-user-service-bugfix.md", "user-service", True),
        ("003-config-chore.md", "order-service", True),
    ],
)
def test_example_issues_parse(filename, expected_service, expected_ready):
    path = EXAMPLES_DIR / filename
    result = parse_issue_file(path)
    assert result.ready is expected_ready
    assert result.spec is not None
    assert result.spec["service"]["name"] == expected_service
    assert not any(e for e in result.errors if not e.startswith("warning:"))


def test_bugfix_without_reproduction_not_ready():
    markdown = """\
---
opspulse_version: "1"
type: bugfix
service:
  name: user-service
runtime:
  jdk_base_image: eclipse-temurin:8-jre
build:
  command: mvn package
  artifact: target/user-service.jar
deploy:
  env: dev
acceptance:
  - id: AC-1
    given: bug is fixed
    then: no NPE on login
---

## 背景
User login throws NPE without reproduction section.
"""
    result = parse_issue_markdown(markdown, schema=SCHEMA)
    assert result.ready is False
    assert any("reproduction steps" in error for error in result.errors)


def test_bugfix_with_repro_keyword_ready():
    markdown = """\
---
opspulse_version: "1"
type: bugfix
service:
  name: user-service
runtime:
  jdk_base_image: eclipse-temurin:8-jre
build:
  command: mvn package
  artifact: target/user-service.jar
deploy:
  env: dev
acceptance:
  - id: AC-1
    given: bug is fixed
    then: no NPE on login
---

## 背景
线上 NPE。复现：POST /api/login 空密码。
"""
    result = parse_issue_markdown(markdown, schema=SCHEMA)
    assert result.ready is True


def test_label_fallback_fills_missing_type():
    spec = {
        "opspulse_version": "1",
        "service": {"name": "order-service"},
        "runtime": {"jdk_base_image": "eclipse-temurin:8-jre"},
        "build": {"command": "mvn package", "artifact": "target/a.jar"},
        "deploy": {"env": "dev"},
        "acceptance": [{"id": "AC-1", "given": "g", "then": "t"}],
    }
    merged = apply_label_fallbacks(spec, ["opspulse:auto", "type:feature", "scope:api"])
    assert merged["type"] == "feature"
    assert merged["scope"] == "api"


def test_invalid_frontmatter_not_ready():
    result = parse_issue_markdown("# no frontmatter\nbody only")
    assert result.ready is False
    assert result.spec is None
    assert result.errors
