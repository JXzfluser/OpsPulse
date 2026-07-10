"""工作流引擎和节点单元测试"""
import sys
from pathlib import Path

SRC = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, SRC)

from opspulse_mcp.workflow_pkg.node import (
    WorkflowNode,
    NodeStatus,
    FailureStrategy,
    NodeResult,
    run_workflow,
)
from opspulse_mcp.workflow_pkg.engine import WorkflowEngine, create_workflow


class TestWorkflowNode:
    """测试工作流节点"""

    def test_node_creation_defaults(self):
        node = WorkflowNode(id="test", name="Test Node", command="echo hello")
        assert node.id == "test"
        assert node.name == "Test Node"
        assert node.auto is False
        assert node.timeout == 300
        assert node.on_failure == FailureStrategy.CONTINUE
        assert node.requires_approval is False
        assert node.status == NodeStatus.PENDING

    def test_node_creation_with_custom_values(self):
        node = WorkflowNode(
            id="test",
            name="Test Node",
            command="echo hello",
            auto=True,
            timeout=600,
            on_failure=FailureStrategy.ABORT,
            requires_approval=True,
            description="A test node",
            icon="🧪",
        )
        assert node.auto is True
        assert node.timeout == 600
        assert node.on_failure == FailureStrategy.ABORT
        assert node.requires_approval is True
        assert node.description == "A test node"
        assert node.icon == "🧪"

    def test_node_execute_success(self):
        node = WorkflowNode(id="test", name="Test", command="echo success", auto=True)
        result = node.execute()
        assert result.status == NodeStatus.COMPLETED
        assert "success" in result.output

    def test_node_execute_failure(self):
        node = WorkflowNode(id="test", name="Test", command="exit 1", auto=True)
        result = node.execute()
        assert result.status == NodeStatus.FAILED

    def test_node_execute_timeout(self):
        node = WorkflowNode(id="test", name="Test", command="sleep 10", auto=True, timeout=1)
        result = node.execute()
        assert result.status == NodeStatus.FAILED
        assert "超时" in result.error

    def test_node_str_representation(self):
        node = WorkflowNode(id="test", name="Test Node", command="echo hello")
        node.status = NodeStatus.COMPLETED
        assert "✅" in str(node)
        assert "Test Node" in str(node)

    def test_node_str_pending(self):
        node = WorkflowNode(id="test", name="Test Node", command="echo hello")
        assert "⬜" in str(node)


class TestRunWorkflow:
    """测试工作流执行"""

    def test_run_empty_workflow(self):
        results = run_workflow([])
        assert results == []

    def test_run_single_node_success(self):
        nodes = [WorkflowNode(id="test", name="Test", command="echo ok", auto=True)]
        results = run_workflow(nodes)
        assert len(results) == 1
        assert results[0].status == NodeStatus.COMPLETED

    def test_run_multiple_nodes(self):
        nodes = [
            WorkflowNode(id="a", name="Step A", command="echo a", auto=True),
            WorkflowNode(id="b", name="Step B", command="echo b", auto=True),
            WorkflowNode(id="c", name="Step C", command="echo c", auto=True),
        ]
        results = run_workflow(nodes)
        assert len(results) == 3
        assert all(r.status == NodeStatus.COMPLETED for r in results)

    def test_run_aborts_on_failure_with_abort_strategy(self):
        nodes = [
            WorkflowNode(id="a", name="Step A", command="echo ok", auto=True),
            WorkflowNode(id="b", name="Step B", command="exit 1", auto=True, on_failure=FailureStrategy.ABORT),
            WorkflowNode(id="c", name="Step C", command="echo c", auto=True),
        ]
        results = run_workflow(nodes)
        assert len(results) == 2, "应在第二个节点中止，不执行第三个"
        assert results[1].status == NodeStatus.FAILED


class TestDryRun:
    """测试干跑模式"""

    def test_dry_run_does_not_execute(self):
        node = WorkflowNode(id="test", name="Test", command="echo should_not_run", auto=True)
        result = node.execute(dry_run=True)
        assert result.status == NodeStatus.COMPLETED
        assert "[DRY RUN]" in result.output

    def test_dry_run_shows_command(self):
        node = WorkflowNode(id="test", name="Test", command="echo hello", auto=True)
        result = node.execute(dry_run=True)
        assert "[DRY RUN]" in result.output


class TestWorkflowEngine:
    """测试工作流引擎"""

    def test_create_workflow_with_template(self):
        engine = create_workflow("tdd", "/root/.hermes/projects/ops-pulse")
        assert engine.template_name == "tdd"
        assert engine.template["name"] == "TDD 测试驱动开发"

    def test_build_nodes(self):
        engine = create_workflow("tdd", "/root/.hermes/projects/ops-pulse")
        nodes = engine.build_nodes()
        assert len(nodes) == 12

    def test_visualize_output(self):
        engine = create_workflow("normal", "/root/.hermes/projects/ops-pulse")
        nodes = engine.build_nodes()
        vis = engine.visualize()
        assert "工作流执行进度" in vis
        assert "标准开发流程" in vis
        assert "[" in vis  # 进度条

    def test_visualize_with_completed_nodes(self):
        engine = create_workflow("tdd", "/root/.hermes/projects/ops-pulse")
        nodes = engine.build_nodes()
        nodes[0].status = NodeStatus.COMPLETED
        nodes[1].status = NodeStatus.RUNNING
        vis = engine.visualize()
        assert "✅" in vis
        assert "⏳" in vis

    def test_load_project_config_no_file(self):
        from opspulse_mcp.workflow_pkg.engine import load_project_config
        config = load_project_config("/tmp")
        assert config == {}

    def test_load_project_config_with_file(self):
        from opspulse_mcp.workflow_pkg.engine import load_project_config
        config = load_project_config("/root/.hermes/projects/ops-pulse")
        assert config is not None
        assert "project" in config


class TestIssueWorkflow:
    """测试旧版工作流状态机"""

    def test_initial_state(self):
        from opspulse_mcp.workflow import IssueWorkflow, IssueState
        wf = IssueWorkflow(1, "test", "repo")
        assert wf.current() == "CREATED"
        assert len(wf.history) == 0

    def test_transition(self):
        from opspulse_mcp.workflow import IssueWorkflow
        wf = IssueWorkflow(1, "test", "repo")
        assert wf.transition("review") is True
        assert wf.current() == "REVIEW_PENDING"

    def test_can_transition(self):
        from opspulse_mcp.workflow import IssueWorkflow
        wf = IssueWorkflow(1, "test", "repo")
        possible = wf.can_transition("review")
        assert "REVIEW_PENDING" in possible

    def test_invalid_transition(self):
        from opspulse_mcp.workflow import IssueWorkflow
        wf = IssueWorkflow(1, "test", "repo")
        assert wf.transition("invalid_action") is False

    def test_history_summary(self):
        from opspulse_mcp.workflow import IssueWorkflow
        wf = IssueWorkflow(45, "test", "repo")
        wf.transition("review")
        wf.transition("approve")
        summary = wf.history_summary()
        assert "Issue #45" in summary
        assert "REVIEW_PENDING" in summary
        assert "REVIEW_PASS" in summary
