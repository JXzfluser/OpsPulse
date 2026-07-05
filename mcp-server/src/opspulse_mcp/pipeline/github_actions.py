"""Resolve GitHub Actions workflow_dispatch targets from Issue Spec + opspulse.yaml."""

from __future__ import annotations

from typing import Any


def _repo_key(owner: str, repo: str) -> str:
    return f"{owner}/{repo}"


def resolve_github_actions_dispatch(
    pipeline_id: str,
    *,
    spec: dict[str, Any] | None,
    config: dict[str, Any],
    owner: str | None = None,
    repo: str | None = None,
    ref: str | None = None,
    variables: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return owner, repo, ref, workflow, inputs for workflow_dispatch."""
    spec = spec or {}
    variables = variables or {}

    repository = spec.get("repository") or {}
    ci = spec.get("ci") or {}

    resolved_owner = owner or repository.get("owner")
    resolved_repo = repo or repository.get("name")
    if not resolved_owner or not resolved_repo:
        raise ValueError(
            "github-actions mode requires owner/repo via arguments or "
            "issue spec repository.owner / repository.name"
        )

    ga = (config.get("pipeline") or {}).get("github_actions") or {}
    repo_configs = ga.get("repositories") or {}
    repo_cfg = repo_configs.get(_repo_key(resolved_owner, resolved_repo)) or {}

    workflow = ci.get("workflow") or repo_cfg.get("workflow")
    if not workflow:
        raise ValueError(
            f"No workflow configured for {_repo_key(resolved_owner, resolved_repo)}; "
            "set issue spec ci.workflow or opspulse.yaml pipeline.github_actions.repositories"
        )

    resolved_ref = ref or repository.get("ref") or ci.get("ref") or ga.get("ref") or "main"

    inputs: dict[str, str] = {}
    pipeline_inputs = (repo_cfg.get("pipelines") or {}).get(pipeline_id, {}).get("inputs") or {}
    inputs.update({k: str(v) for k, v in pipeline_inputs.items()})

    spec_inputs = ci.get("inputs") or {}
    inputs.update({k: str(v) for k, v in spec_inputs.items()})

    service_input_key = repo_cfg.get("service_input")
    service_name = (spec.get("service") or {}).get("name")
    if service_input_key and service_name:
        inputs.setdefault(service_input_key, str(service_name))

    inputs.update({k: str(v) for k, v in variables.items()})

    return {
        "owner": resolved_owner,
        "repo": resolved_repo,
        "ref": resolved_ref,
        "workflow": workflow,
        "inputs": inputs,
    }
