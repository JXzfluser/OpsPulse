"""Extract YAML frontmatter and body from Issue markdown."""

from __future__ import annotations

import re

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
REPRODUCTION_MARKERS = (
    "## 复现步骤",
    "## Reproduction Steps",
    "## Steps to Reproduce",
)
REPRODUCTION_KEYWORDS = ("复现", "重现")


def extract_frontmatter(markdown: str) -> tuple[dict | None, str]:
    """Return (spec dict, error message). Error is empty on success."""
    match = FRONTMATTER_RE.match(markdown.strip())
    if not match:
        return None, "Missing YAML frontmatter block (expected --- at file start)"
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return None, f"Invalid YAML frontmatter: {exc}"
    if not isinstance(data, dict):
        return None, "Frontmatter must be a YAML mapping"
    return data, ""


def extract_body(markdown: str) -> str:
    return FRONTMATTER_RE.sub("", markdown.strip(), count=1).strip()


def has_reproduction_steps(markdown: str) -> bool:
    """True when bugfix body includes reproduction section or 复现/重现 keywords."""
    body = extract_body(markdown)
    if any(marker in body for marker in REPRODUCTION_MARKERS):
        return True
    return any(keyword in body for keyword in REPRODUCTION_KEYWORDS)
