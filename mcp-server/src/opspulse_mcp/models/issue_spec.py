"""Pydantic models for Issue Spec and parse results."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AcceptanceCriterion(BaseModel):
    id: str
    given: str
    then: str


class IssueSpec(BaseModel):
    opspulse_version: str
    type: Literal["feature", "bugfix", "chore", "infra"]
    service: dict[str, Any]
    runtime: dict[str, Any]
    build: dict[str, Any]
    deploy: dict[str, Any]
    acceptance: list[AcceptanceCriterion]
    scope: str | None = None
    priority: str | None = None
    harness: dict[str, Any] | None = None
    affected_paths: list[str] | None = None

    model_config = {"extra": "forbid"}


class ParseIssueResult(BaseModel):
    spec: dict[str, Any] | None = None
    raw_body: str = ""
    labels: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    ready: bool = False


IssueState = Literal["parsed", "in-dev", "pr-open", "testing", "deployed", "failed"]
PipelineId = Literal["pr-validation", "deploy-dev", "deploy-staging"]
PipelineMode = Literal["local", "harness", "github-actions"]
