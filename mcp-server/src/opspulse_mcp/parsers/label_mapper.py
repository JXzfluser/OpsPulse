"""Map GitHub labels to Issue Spec fields when frontmatter is incomplete."""

from __future__ import annotations

import copy
from typing import Any


def _label_value(label: str, prefix: str) -> str | None:
    needle = f"{prefix}:"
    if label.startswith(needle):
        return label[len(needle) :]
    return None


def apply_label_fallbacks(spec: dict[str, Any], labels: list[str]) -> dict[str, Any]:
    """Merge label-derived values into spec (labels do not override frontmatter)."""
    merged = copy.deepcopy(spec)

    for label in labels:
        if label == "opspulse:auto":
            continue

        if value := _label_value(label, "type"):
            merged.setdefault("type", value)
        elif value := _label_value(label, "scope"):
            merged.setdefault("scope", value)
        elif value := _label_value(label, "component"):
            service = merged.setdefault("service", {})
            if isinstance(service, dict):
                service.setdefault("name", value)
        elif value := _label_value(label, "priority"):
            merged.setdefault("priority", value)
        elif value := _label_value(label, "pipeline"):
            harness = merged.setdefault("harness", {})
            if isinstance(harness, dict):
                harness.setdefault("pipeline", value)
        elif value := _label_value(label, "env"):
            deploy = merged.setdefault("deploy", {})
            if isinstance(deploy, dict):
                deploy.setdefault("env", value)

    return merged
