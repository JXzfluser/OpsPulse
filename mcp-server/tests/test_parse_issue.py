"""Tests for parse_issue tool."""

from __future__ import annotations

from pathlib import Path

import pytest

from opspulse_mcp.parsers.label_mapper import apply_label_fallbacks
from opspulse_mcp.parsers.validation import load_schema
from opspulse_mcp.tools.parse_issue import parse_issue_file, parse_issue_markdown

SCHEMA = load_schema()


def test_parse_issue_file_with_inline_markdown():
    """验证 parse_issue_file 能解析带 frontmatter 的 Issue 文档"""
    import tempfile
    markdown = """---
opspulse_version: "1"
type: feature
service:
  name: order-service
runtime:
  jdk_base_image: eclipse-temurin:8-jre
build:
  command: mvn package
  artifact: target/order-service.jar
deploy:
  env: dev
acceptance:
  - id: AC-1
    given: user is authenticated
    then: order is created
---

## 需求
创建订单 API，支持多支付方式。

## 影响路径
- src/api/orders.py
- src/services/payment.py
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(markdown)
        f.flush()
        result = parse_issue_file(Path(f.name))
    assert result.ready is True
    assert result.spec is not None
    assert result.spec["service"]["name"] == "order-service"
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
