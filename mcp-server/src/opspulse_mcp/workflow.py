"""OpsPulse 完整交付闭环状态机"""
from __future__ import annotations

from enum import Enum, auto
from typing import Any, Optional


class IssueState(Enum):
    """Issue 生命周期状态"""
    CREATED = auto()
    REVIEW_PENDING = auto()
    REVIEW_PASS = auto()
    REVIEW_REJECT = auto()
    DESIGN_PENDING = auto()
    DESIGN_APPROVED = auto()
    DESIGN_REJECTED = auto()
    BREAKDOWN_DONE = auto()
    CODING_IN_PROGRESS = auto()
    CODING_DONE = auto()
    PR_CREATED = auto()
    PR_VERIFYING = auto()
    PR_VERIFIED = auto()
    PR_FAILED = auto()
    SMOKE_TESTING = auto()
    SMOKE_PASS = auto()
    SMOKE_FAILED = auto()
    DEPLOYING = auto()
    DEPLOYED = auto()
    ROLLBACK = auto()
    CLOSED = auto()


# 状态转移规则：(from_state, to_state, required_action)
TRANSITIONS = {
    (IssueState.CREATED, IssueState.REVIEW_PENDING, "review"): None,
    (IssueState.REVIEW_PENDING, IssueState.REVIEW_PASS, "approve"): None,
    (IssueState.REVIEW_PENDING, IssueState.REVIEW_REJECT, "reject"): None,
    (IssueState.REVIEW_REJECT, IssueState.REVIEW_PENDING, "revise"): None,
    (IssueState.REVIEW_PASS, IssueState.DESIGN_PENDING, "design"): None,
    (IssueState.DESIGN_PENDING, IssueState.DESIGN_APPROVED, "approve"): None,
    (IssueState.DESIGN_PENDING, IssueState.DESIGN_REJECTED, "reject"): None,
    (IssueState.DESIGN_REJECTED, IssueState.DESIGN_PENDING, "revise"): None,
    (IssueState.DESIGN_APPROVED, IssueState.BREAKDOWN_DONE, "breakdown"): None,
    (IssueState.BREAKDOWN_DONE, IssueState.CODING_IN_PROGRESS, "start_coding"): None,
    (IssueState.CODING_IN_PROGRESS, IssueState.CODING_DONE, "finish_coding"): None,
    (IssueState.CODING_DONE, IssueState.PR_CREATED, "create_pr"): None,
    (IssueState.PR_CREATED, IssueState.PR_VERIFYING, "verify"): None,
    (IssueState.PR_VERIFYING, IssueState.PR_VERIFIED, "pass"): None,
    (IssueState.PR_VERIFYING, IssueState.PR_FAILED, "fail"): None,
    (IssueState.PR_FAILED, IssueState.CODING_IN_PROGRESS, "fix"): None,
    (IssueState.PR_VERIFIED, IssueState.SMOKE_TESTING, "smoke_test"): None,
    (IssueState.SMOKE_TESTING, IssueState.SMOKE_PASS, "pass"): None,
    (IssueState.SMOKE_TESTING, IssueState.SMOKE_FAILED, "fail"): None,
    (IssueState.SMOKE_FAILED, IssueState.CODING_IN_PROGRESS, "fix"): None,
    (IssueState.SMOKE_PASS, IssueState.DEPLOYING, "deploy"): None,
    (IssueState.DEPLOYING, IssueState.DEPLOYED, "success"): None,
    (IssueState.DEPLOYING, IssueState.ROLLBACK, "fail"): None,
    (IssueState.ROLLBACK, IssueState.DEPLOYING, "retry"): None,
    (IssueState.DEPLOYED, IssueState.CLOSED, "close"): None,
}


class TransitionError(Exception):
    """状态转移失败"""
    pass


class IssueWorkflow:
    """Issue 交付工作流状态机"""

    def __init__(self, issue_number: int, owner: str, repo: str):
        self.issue_number = issue_number
        self.owner = owner
        self.repo = repo
        self.current_state = IssueState.CREATED
        self.history: list[dict[str, Any]] = []

    def transition(self, action: str) -> bool:
        """尝试状态转移"""
        for (from_state, to_state, required_action) in TRANSITIONS:
            if from_state == self.current_state and required_action == action:
                old_state = self.current_state
                self.current_state = to_state
                self.history.append({
                    "from": old_state.name,
                    "to": to_state.name,
                    "action": action,
                })
                return True
        return False

    def can_transition(self, action: str) -> list[str]:
        """返回当前状态下可以通过的动作"""
        possible = []
        for (from_state, to_state, required_action) in TRANSITIONS:
            if from_state == self.current_state and required_action == action:
                possible.append(to_state.name)
        return possible

    def current(self) -> str:
        return self.current_state.name

    def history_summary(self) -> str:
        lines = [f"Issue #{self.issue_number} 当前状态: {self.current_state.name}"]
        lines.append(f"转移历史 ({len(self.history)} 次):")
        for h in self.history:
            lines.append(f"  {h['from']} → {h['to']} (via {h['action']})")
        return "\n".join(lines)
