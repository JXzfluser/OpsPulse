"""Tests for scripts/validate-issue-spec.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate-issue-spec.py"

_spec = importlib.util.spec_from_file_location("validate_issue_spec", VALIDATOR_PATH)
assert _spec and _spec.loader
_validator = importlib.util.module_from_spec(_spec)
sys.modules["validate_issue_spec"] = _validator
_spec.loader.exec_module(_validator)

extract_frontmatter = _validator.extract_frontmatter
has_reproduction_steps = _validator.has_reproduction_steps
load_schema = _validator.load_schema
validate_issue_spec = _validator.validate_issue_spec

SCHEMA = load_schema()
EXAMPLES_DIR = REPO_ROOT / "examples" / "issues"


VALID_FEATURE = """\
---
opspulse_version: "1"
type: feature
scope: api
service:
  name: order-service
  module_path: services/order-service/
runtime:
  jdk_base_image: eclipse-temurin:8-jre
build:
  tool: maven
  jdk: "1.8"
  command: mvn -pl services/order-service -am package -DskipTests
  artifact: services/order-service/target/order-service.jar
deploy:
  env: dev
acceptance:
  - id: AC-1
    given: service is running
    then: health endpoint returns UP
---

## 背景
Demo feature issue.
"""


def test_valid_feature_frontmatter_passes_schema():
    errors = validate_issue_spec(VALID_FEATURE, schema=SCHEMA)
    assert errors == []


def test_missing_required_field_fails():
    markdown = """\
---
opspulse_version: "1"
type: feature
service:
  name: order-service
runtime:
  jdk_base_image: eclipse-temurin:8-jre
build:
  command: mvn package
  artifact: target/app.jar
acceptance:
  - id: AC-1
    given: x
    then: y
---

## 背景
Missing deploy.env.
"""
    errors = validate_issue_spec(markdown, schema=SCHEMA)
    assert any("deploy" in error for error in errors)


def test_bugfix_without_reproduction_steps_fails():
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
User login throws NPE.
"""
    errors = validate_issue_spec(markdown, schema=SCHEMA)
    assert any("reproduction steps" in error for error in errors)


def test_bugfix_with_reproduction_steps_passes():
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

## 复现步骤
1. POST /api/login with empty password
2. Observe 500 error
"""
    errors = validate_issue_spec(markdown, schema=SCHEMA)
    assert errors == []


def test_example_issue_files_validate():
    for issue_file in sorted(EXAMPLES_DIR.glob("*.md")):
        errors = validate_issue_spec(issue_file.read_text(encoding="utf-8"), schema=SCHEMA)
        assert errors == [], f"{issue_file.name}: {errors}"


def test_extract_frontmatter_returns_mapping():
    spec, error = extract_frontmatter(VALID_FEATURE)
    assert error == ""
    assert spec is not None
    assert spec["service"]["name"] == "order-service"


def test_has_reproduction_steps_detects_chinese_heading():
    body = "## 复现步骤\n1. Do something"
    assert has_reproduction_steps(f"---\nopspulse_version: '1'\n---\n{body}")
