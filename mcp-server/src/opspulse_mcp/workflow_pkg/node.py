"""工作流节点定义与执行"""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class NodeStatus(Enum):
    PENDING = "⬜"
    RUNNING = "⏳"
    COMPLETED = "✅"
    FAILED = "❌"
    WAITING_APPROVAL = "⏸️"
    ABORTED = "🛑"
    ROLLBACK = "↩️"


class FailureStrategy(Enum):
    ABORT = "abort"
    ROLLBACK = "rollback"
    CONTINUE = "continue"


@dataclass
class NodeResult:
    node_id: str
    status: NodeStatus
    duration: float = 0.0
    output: str = ""
    error: str = ""
    approved: bool = False


@dataclass
class WorkflowNode:
    """工作流节点"""
    id: str
    name: str
    command: str
    auto: bool = False
    timeout: int = 300
    on_failure: FailureStrategy = FailureStrategy.CONTINUE
    requires_approval: bool = False
    description: str = ""
    icon: str = "🔹"
    
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[NodeResult] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    
    def execute(self, dry_run: bool = False) -> NodeResult:
        """执行节点"""
        self.status = NodeStatus.RUNNING
        self.started_at = time.time()
        
        if self.requires_approval and not self.auto:
            self.status = NodeStatus.WAITING_APPROVAL
            approved = self._wait_for_approval()
            if not approved:
                self.status = NodeStatus.ABORTED
                return NodeResult(self.id, NodeStatus.ABORTED, error="审批被拒绝")
        
        if dry_run:
            print(f"  📝 [DRY RUN] {self.icon} {self.name}")
            print(f"     命令: {self.command}")
            print(f"     超时: {self.timeout}s")
            self.status = NodeStatus.COMPLETED
            return NodeResult(self.id, NodeStatus.COMPLETED, output="[DRY RUN]")
        
        try:
            result = subprocess.run(
                self.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            self.finished_at = time.time()
            duration = self.finished_at - self.started_at
            
            if result.returncode == 0:
                self.status = NodeStatus.COMPLETED
                return NodeResult(
                    self.id, NodeStatus.COMPLETED,
                    duration=duration,
                    output=result.stdout[:500],
                )
            else:
                self.status = NodeStatus.FAILED
                node_result = NodeResult(
                    self.id, NodeStatus.FAILED,
                    duration=duration,
                    error=result.stderr[:500],
                )
                
                if self.on_failure == FailureStrategy.ABORT:
                    self.status = NodeStatus.ABORTED
                    node_result.error += "\n💡 失败策略: 中止流程"
                elif self.on_failure == FailureStrategy.ROLLBACK:
                    self.status = NodeStatus.ROLLBACK
                    node_result.error += "\n💡 失败策略: 回滚到上一个成功节点"
                
                return node_result
                
        except subprocess.TimeoutExpired:
            self.status = NodeStatus.FAILED
            return NodeResult(self.id, NodeStatus.FAILED, error=f"超时 ({self.timeout}s)")
        except Exception as e:
            self.status = NodeStatus.FAILED
            return NodeResult(self.id, NodeStatus.FAILED, error=str(e))
    
    def _wait_for_approval(self) -> bool:
        """等待人工审批"""
        print(f"\n  ⏸️  节点 '{self.name}' 需要人工审批")
        print(f"  命令: {self.command}")
        print(f"  描述: {self.description or '无'}")
        print(f"\n  输入 'y' 批准，'n' 拒绝: ", end="", flush=True)
        
        try:
            response = input().strip().lower()
            return response == 'y'
        except (EOFError, KeyboardInterrupt):
            return False
    
    def __str__(self) -> str:
        """终端可视化"""
        icon = self.status.value
        return f"{icon} {self.name}"


def run_workflow(nodes: list[WorkflowNode], dry_run: bool = False) -> list[NodeResult]:
    """执行工作流"""
    results = []
    
    for node in nodes:
        print(f"\n  [{node.icon}] 执行节点: {node.name}")
        result = node.execute(dry_run=dry_run)
        results.append(result)
        
        if result.status == NodeStatus.ABORTED:
            print(f"\n  🛑 工作流中止: {node.name}")
            break
        elif result.status == NodeStatus.FAILED:
            print(f"\n  ❌ 节点失败: {node.name}")
            if node.on_failure == FailureStrategy.ROLLBACK:
                print(f"  ↩️  回滚到上一个成功节点")
            elif node.on_failure == FailureStrategy.ABORT:
                print(f"  🛑 中止工作流")
                break
    
    return results
