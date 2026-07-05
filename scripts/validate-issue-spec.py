#!/usr/bin/env python3
"""Validate OpsPulse Issue Spec YAML frontmatter against schemas/issue-spec.v1.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_SRC = REPO_ROOT / "mcp-server" / "src"
if str(MCP_SRC) not in sys.path:
    sys.path.insert(0, str(MCP_SRC))

try:
    from opspulse_mcp.parsers.frontmatter import extract_frontmatter, has_reproduction_steps
    from opspulse_mcp.parsers.validation import load_schema, validate_spec_dict
except ImportError as exc:
    print(
        "Missing dependency: install mcp-server with `cd mcp-server && uv sync`",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


def validate_issue_spec(markdown: str, schema: dict | None = None) -> list[str]:
    """Return a list of validation errors; empty list means valid."""
    spec, frontmatter_error = extract_frontmatter(markdown)
    if frontmatter_error:
        return [frontmatter_error]
    assert spec is not None
    return validate_spec_dict(spec, markdown=markdown, schema=schema)


def validate_file(path: Path, schema: dict | None = None) -> list[str]:
    markdown = path.read_text(encoding="utf-8")
    return validate_issue_spec(markdown, schema=schema)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Markdown issue files with YAML frontmatter",
    )
    args = parser.parse_args(argv)

    schema = load_schema()
    exit_code = 0

    for file_path in args.files:
        if not file_path.exists():
            print(f"FAIL {file_path}: file not found", file=sys.stderr)
            exit_code = 1
            continue

        errors = validate_file(file_path, schema=schema)
        if errors:
            exit_code = 1
            print(f"FAIL {file_path}", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
        else:
            print(f"OK {file_path}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
