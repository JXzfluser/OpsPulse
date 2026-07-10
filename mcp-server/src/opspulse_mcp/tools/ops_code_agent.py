"""AI 编码桥接 Tool — 对接 Claude Code / Codex / Cursor Agent 自动编码"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from opspulse_mcp.workflow import IssueWorkflow


def _build_code_prompt(
    spec: dict,
    design_summary: str | None = None,
    breakdown: list[dict] | None = None,
) -> str:
    """Build a coding prompt for the AI agent."""
    service = spec.get("service", {}).get("name", "unknown")
    issue_type = spec.get("type", "feature")
    acceptance = spec.get("acceptance", [])
    affected_paths = spec.get("affected_paths", [])

    prompt = f"""You are a senior developer working on a {issue_type} for service: `{service}`.

## Issue Requirements
- Type: {issue_type}
- Priority: {spec.get('priority', 'N/A')}
- Scope: {spec.get('scope', 'N/A')}

## Acceptance Criteria
"""
    for ac in acceptance:
        prompt += f"- **{ac.get('id', '?')}**: Given \"{ac.get('given', '')}\", then \"{ac.get('then', '')}\"\n"

    if affected_paths:
        prompt += f"\n## Affected Paths\nThese files may be modified:\n"
        for p in affected_paths:
            prompt += f"- `{p}`\n"

    if design_summary:
        prompt += f"\n## Design Summary\n{design_summary}\n"

    if breakdown:
        prompt += "\n## Task Breakdown\n"
        for i, task in enumerate(breakdown, 1):
            prompt += f"{i}. {task.get('title', task.get('description', 'Task'))}\n"

    prompt += f"""\n## Instructions
1. Read the existing code in the affected paths
2. Implement the changes to meet all acceptance criteria
3. Write tests for new functionality
4. Ensure existing tests still pass
5. Commit with conventional commit message: "feat({service}): ..."

Return your work as a JSON object with:
- "files_changed": list of file paths modified
- "tests_added": list of test file paths
- "commit_message": the commit message used
- "status": "success" or "failed"
- "error": error message if failed
"""
    return prompt


def _invoke_claude_code(prompt: str, workdir: str) -> dict:
    """Invoke Claude Code CLI."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        result = subprocess.run(
            ["claude", "-p", f'<file://{prompt_file}'],
            cwd=workdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
            text=True,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {"error": "claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"}
    except subprocess.TimeoutExpired:
        return {"error": "Claude Code timed out after 300s"}
    finally:
        os.unlink(prompt_file)


def _invoke_codex(prompt: str, workdir: str) -> dict:
    """Invoke OpenAI Codex CLI."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        result = subprocess.run(
            ["codex", prompt_file],
            cwd=workdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
            text=True,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {"error": "codex CLI not found. Install with: npm install -g @openai/codex"}
    except subprocess.TimeoutExpired:
        return {"error": "Codex timed out after 300s"}
    finally:
        os.unlink(prompt_file)


def _invoke_custom_agent(command: list[str], prompt: str, workdir: str) -> dict:
    """Invoke a custom coding agent with a prompt file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        cmd = command + [prompt_file]
        result = subprocess.run(
            cmd,
            cwd=workdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
            text=True,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {"error": f"Command not found: {command[0]}"}
    except subprocess.TimeoutExpired:
        return {"error": "Custom agent timed out after 300s"}
    finally:
        os.unlink(prompt_file)


def ops_code_agent(
    issue_number: int,
    owner: str,
    repo: str,
    spec: dict,
    design_summary: str | None = None,
    breakdown: list[dict] | None = None,
    agent: str = "claude-code",
    workdir: str | None = None,
    custom_command: list[str] | None = None,
) -> dict[str, Any]:
    """AI 编码桥接：自动调用 AI Agent 完成编码任务。

    Args:
        issue_number: Issue 编号
        owner: GitHub owner
        repo: GitHub repo name
        spec: Issue Spec 字典
        design_summary: 设计方案摘要
        breakdown: 任务拆分列表
        agent: 编码代理 ("claude-code" / "codex" / "custom")
        workdir: 工作目录（可选，默认当前目录）
        custom_command: 自定义命令（agent=custom 时使用）

    Returns:
        编码结果和状态转移
    """
    workflow = IssueWorkflow(issue_number, owner, repo)

    # 1. 构建编码 prompt
    prompt = _build_code_prompt(spec, design_summary, breakdown)

    # 2. 选择执行器
    if agent == "claude-code":
        executor = _invoke_claude_code
    elif agent == "codex":
        executor = _invoke_codex
    elif agent == "custom" and custom_command:
        executor = lambda p, w: _invoke_custom_agent(custom_command, p, w)
    else:
        return {
            "success": False,
            "error": f"Unknown agent: {agent}. Use 'claude-code', 'codex', or 'custom' with custom_command.",
        }

    # 3. 执行编码
    workdir = workdir or os.getcwd()
    result = executor(prompt, workdir)

    # 4. 解析结果
    coding_success = result.get("returncode", 1) == 0

    # 5. 状态转移
    transition_success = None
    if coding_success:
        transition_success = workflow.transition("coding_done")

    return {
        "success": coding_success,
        "agent": agent,
        "coding_result": result,
        "transition": {
            "success": transition_success,
            "from": "BREAKDOWN_DONE",
            "to": "CODING_DONE",
        },
        "workflow": workflow.history_summary(),
    }