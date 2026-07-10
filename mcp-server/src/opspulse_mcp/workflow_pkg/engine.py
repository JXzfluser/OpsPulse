"""工作流引擎 — 加载模板、合并配置、执行节点"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

from opspulse_mcp.templates import list_builtin_templates, resolve_template
from opspulse_mcp.workflow_pkg.node import (
    WorkflowNode,
    NodeStatus,
    FailureStrategy,
    run_workflow,
)


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self, template_name: str, project_config: Optional[dict] = None):
        self.template_name = template_name
        self.project_config = project_config or {}
        self.template = self._load_template(template_name)
        self.nodes: list[WorkflowNode] = []
    
    def _load_template(self, template_name: str) -> dict:
        """加载模板（内置 + 项目级覆盖）"""
        builtin = list_builtin_templates()
        if template_name not in builtin:
            raise ValueError(f"内置模板 '{template_name}' 不存在。可用模板: {', '.join(builtin)}")
        
        return resolve_template(template_name, self.project_config)
    
    def build_nodes(self) -> list[WorkflowNode]:
        """从模板构建节点列表"""
        stages = self.template.get("stages", [])
        nodes = []
        
        for stage in stages:
            node = WorkflowNode(
                id=stage["id"],
                name=stage["name"],
                command=stage.get("command", "echo 'no command'"),
                auto=stage.get("auto", False),
                timeout=stage.get("timeout", 300),
                on_failure=FailureStrategy(stage.get("on_failure", "continue")),
                requires_approval=stage.get("requires_approval", False),
                description=stage.get("description", ""),
                icon=stage.get("icon", "🔹"),
            )
            nodes.append(node)
        
        self.nodes = nodes
        return nodes
    
    def execute(self, dry_run: bool = False) -> list[Any]:
        """执行工作流"""
        if not self.nodes:
            self.build_nodes()
        
        return run_workflow(self.nodes, dry_run=dry_run)
    
    def visualize(self) -> str:
        """终端可视化进度"""
        if not self.nodes:
            self.build_nodes()
        
        template_name = self.template.get("name", self.template_name)
        template_icon = self.template.get("icon", "🔹")
        
        lines = [
            "",
            "╔══════════════════════════════════════════════════════════╗",
            "║                    工作流执行进度                         ║",
            "╚══════════════════════════════════════════════════════════╝",
            "",
            f"  {template_icon} {template_name}",
            "",
        ]
        
        completed = sum(1 for n in self.nodes if n.status == NodeStatus.COMPLETED)
        total = len(self.nodes)
        progress = completed / total if total > 0 else 0
        
        bar_length = 40
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        lines.append(f"  [{bar}] {progress:.0%}")
        lines.append("")
        
        for i, node in enumerate(self.nodes, 1):
            status_icon = node.status.value if node.status else "⬜"
            lines.append(f"  {i:2d}. {status_icon} {node.name}")
        
        lines.append("")
        
        current = next((n for n in self.nodes if n.status == NodeStatus.RUNNING), None)
        if current:
            lines.append(f"  当前节点: {current.name}")
        
        waiting = next((n for n in self.nodes if n.status == NodeStatus.WAITING_APPROVAL), None)
        if waiting:
            lines.append(f"  等待审批: {waiting.name} (requires_approval: true)")
            lines.append(f"  按 Enter 继续审查...")
        
        return "\n".join(lines)


def load_project_config(project_path: str | Path) -> dict:
    """加载项目配置"""
    path = Path(project_path).resolve()
    config_file = path / ".opspulse.yaml"
    
    if not config_file.exists():
        return {}
    
    with config_file.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def create_workflow(template_name: str, project_path: Optional[str] = None) -> WorkflowEngine:
    """创建工作流引擎"""
    project_config = None
    if project_path:
        project_config = load_project_config(project_path)
    
    return WorkflowEngine(template_name, project_config)
