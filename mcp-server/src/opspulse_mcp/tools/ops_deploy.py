"""部署 Tool — 完整功能：灰度发布 + 自动回滚 + 部署验证"""
from __future__ import annotations

import json
import time
from typing import Any

import httpx

from opspulse_mcp.github.client import create_issue_comment
from opspulse_mcp.workflow import IssueWorkflow

# 灰度策略
GRAY_STEPS = [10, 25, 50, 100]
GRAY_OBSERVE_SECONDS = 60  # 每个阶段观察 60 秒


def _check_deployment_health(url: str, error_rate_threshold: float = 0.01) -> dict:
    """检查部署后服务健康状态（模拟）。"""
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)
            status_code = resp.status_code
            # 模拟错误率检查
            error_rate = 0.0 if status_code == 200 else 1.0
            return {
                "healthy": status_code == 200 and error_rate <= error_rate_threshold,
                "status_code": status_code,
                "error_rate": error_rate,
                "threshold": error_rate_threshold,
            }
    except Exception as exc:
        return {"healthy": False, "error": str(exc)}


def _rollback_deployment(owner: str, repo: str, issue_number: int, reason: str) -> dict:
    """触发回滚（通过 GHA rollback workflow）。"""
    token = __import__("os").environ.get("GITHUB_PAT", "")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/cicd.yml/dispatches"
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            url,
            headers=headers,
            json={"ref": "main", "inputs": {"action": "rollback", "reason": reason}},
        )

    return {
        "rolled_back": resp.status_code == 204,
        "reason": reason,
        "status_code": resp.status_code,
    }


def ops_deploy(
    issue_number: int,
    owner: str,
    repo: str,
    environment: str = "prod",
    gray_percentage: int | None = None,
    health_check_url: str | None = None,
    error_rate_threshold: float = 0.01,
    rollback_on_failure: bool = True,
) -> dict[str, Any]:
    """灰度/全量部署，支持自动回滚。

    Args:
        issue_number: Issue 编号
        owner: GitHub owner
        repo: GitHub repo name
        environment: 部署环境 (dev / staging / prod)
        gray_percentage: 灰度百分比 (1-100)，None 则全量
        health_check_url: 健康检查 URL
        error_rate_threshold: 错误率阈值
        rollback_on_failure: 失败时自动回滚

    Returns:
        部署结果和状态转移
    """
    workflow = IssueWorkflow(issue_number, owner, repo)

    results = {
        "issue_number": issue_number,
        "environment": environment,
        "steps": [],
    }

    # 确定灰度策略
    if gray_percentage is None:
        gray_percentage = 100

    # 如果是灰度部署，逐步放量
    if gray_percentage < 100:
        stages = [s for s in GRAY_STEPS if s <= gray_percentage]
    else:
        stages = [100]

    deployment_healthy = True

    for stage in stages:
        step = {
            "stage": stage,
            "action": "deploying",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        # 1. 触发部署（通过 GHA）
        try:
            token = __import__("os").environ.get("GITHUB_PAT", "")
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            }
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/cicd.yml/dispatches"
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    url,
                    headers=headers,
                    json={
                        "ref": "main",
                        "inputs": {
                            "environment": environment,
                            "gray_percentage": str(stage),
                        },
                    },
                )
            step["ci_triggered"] = resp.status_code == 204
            step["ci_status_code"] = resp.status_code
        except Exception as exc:
            step["ci_triggered"] = False
            step["error"] = str(exc)
            deployment_healthy = False

        # 2. 健康检查
        if health_check_url and stage >= stages[-1]:
            health = _check_deployment_health(
                health_check_url, error_rate_threshold
            )
            step["health_check"] = health
            if not health.get("healthy", False):
                deployment_healthy = False
                step["action"] = "unhealthy"
        else:
            step["health_check"] = {"skipped": True}

        results["steps"].append(step)

        # 如果当前阶段失败且需要回滚
        if not deployment_healthy and rollback_on_failure:
            rollback_result = _rollback_deployment(owner, repo, issue_number, f"Stage {stage}% unhealthy")
            results["steps"][-1]["rollback"] = rollback_result
            break

        # 观察期（最后阶段不需要）
        if stage < stages[-1]:
            time.sleep(GRAY_OBSERVE_SECONDS)

    # 3. 状态转移
    transition_success = None
    if deployment_healthy:
        transition_success = workflow.transition("deploy")
        results["deployment_healthy"] = True
    else:
        results["deployment_healthy"] = False

    # 4. 写 Comment 到 Issue
    comment_parts = [
        "## OpsPulse 部署结果",
        "",
        f"**环境**: {environment}",
        f"**灰度策略**: {'全量' if gray_percentage == 100 else '逐步 ' + ' → '.join(map(str, stages)) + '%'}",
        f"**部署状态**: {'✅ 成功' if deployment_healthy else '❌ 失败'}",
        "",
        "### 部署步骤",
    ]

    for i, step in enumerate(results["steps"], 1):
        icon = "✅" if step.get("ci_triggered") else "❌"
        comment_parts.append(f"{i}. {icon} Stage {step['stage']}% — {'成功' if step.get('ci_triggered') else '失败'}")

    if results.get("steps") and "rollback" in results["steps"][-1]:
        rl = results["steps"][-1]["rollback"]
        comment_parts.append(
            f"🔄 已回滚: {rl.get('reason', 'unknown')}"
        )

    comment_parts.extend(["", workflow.history_summary()])

    posted = False
    try:
        create_issue_comment(owner, repo, issue_number, "\n".join(comment_parts))
        posted = True
    except Exception:
        pass

    results["transition"] = {
        "success": transition_success,
        "from": "SMOKE_PASS",
        "to": "DEPLOYING",
    }
    results["posted"] = posted
    results["workflow"] = workflow.history_summary()

    return results