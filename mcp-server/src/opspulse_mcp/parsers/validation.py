"""JSON Schema validation for Issue Spec frontmatter."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from opspulse_mcp.config import find_repo_root, schema_path
from opspulse_mcp.parsers.frontmatter import has_reproduction_steps


def load_schema(path: Path | None = None) -> dict:
    schema_file = path or schema_path(find_repo_root())
    with schema_file.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_spec_dict(
    spec: dict,
    markdown: str = "",
    schema: dict | None = None,
) -> list[str]:
    """Return validation errors; empty list means schema-valid."""
    errors: list[str] = []
    schema = schema or load_schema()

    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(spec), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path) or "(root)"
        errors.append(f"{path}: {error.message}")

    if spec.get("type") == "bugfix" and markdown and not has_reproduction_steps(markdown):
        errors.append(
            "body: bugfix issues must include reproduction steps "
            "(## 复现步骤, ## Reproduction Steps, or 复现/重现 in body)"
        )

    return errors
