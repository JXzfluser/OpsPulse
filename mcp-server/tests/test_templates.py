"""模板系统单元测试"""
import sys
import os
from pathlib import Path

# 确保 src 在路径中
SRC = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, SRC)

from opspulse_mcp.templates import (
    list_builtin_templates,
    load_builtin_template,
    load_project_config,
    resolve_template,
)


class TestListBuiltinTemplates:
    """测试模板列表功能"""

    def test_returns_sorted_list(self):
        templates = list_builtin_templates()
        assert templates == sorted(templates), "模板列表应已排序"

    def test_contains_expected_templates(self):
        templates = list_builtin_templates()
        assert "tdd" in templates
        assert "normal" in templates
        assert "hotfix" in templates
        assert "feature" in templates

    def test_contains_four_templates(self):
        templates = list_builtin_templates()
        assert len(templates) == 4

    def test_all_are_strings(self):
        templates = list_builtin_templates()
        assert all(isinstance(t, str) for t in templates)


class TestLoadBuiltinTemplate:
    """测试模板加载功能"""

    def test_load_tdd_template(self):
        template = load_builtin_template("tdd")
        assert template["name"] == "TDD 测试驱动开发"
        assert "stages" in template
        assert len(template["stages"]) == 12

    def test_load_normal_template(self):
        template = load_builtin_template("normal")
        assert template["name"] == "标准开发流程"
        assert template["icon"] == "⚡"

    def test_load_hotfix_template(self):
        template = load_builtin_template("hotfix")
        assert template["name"] == "紧急修复"
        assert template["icon"] == "🔥"

    def test_load_feature_template(self):
        template = load_builtin_template("feature")
        assert template["name"] == "大型功能开发"
        assert template["icon"] == "🏗️"

    def test_nonexistent_template_raises(self):
        try:
            load_builtin_template("nonexistent")
            assert False, "应抛出 ValueError"
        except ValueError as e:
            assert "不存在" in str(e)

    def test_template_stages_have_required_fields(self):
        template = load_builtin_template("tdd")
        for stage in template["stages"]:
            assert "id" in stage, f"阶段缺少 id: {stage}"
            assert "name" in stage, f"阶段缺少 name: {stage}"
            assert "auto" in stage, f"阶段缺少 auto: {stage}"
            assert "timeout" in stage, f"阶段缺少 timeout: {stage}"


class TestResolveTemplate:
    """测试模板解析（内置 + 项目级覆盖）"""

    def test_resolve_builtin_tdd(self):
        template = resolve_template("tdd")
        assert template["name"] == "TDD 测试驱动开发"
        assert len(template["stages"]) == 12

    def test_resolve_builtin_normal(self):
        template = resolve_template("normal")
        assert template["name"] == "标准开发流程"

    def test_resolve_with_empty_config(self):
        template = resolve_template("tdd", {})
        assert template["name"] == "TDD 测试驱动开发"

    def test_resolve_unknown_template_raises(self):
        try:
            resolve_template("unknown")
            assert False, "应抛出 ValueError"
        except ValueError as e:
            assert "不存在" in str(e)

    def test_custom_stages_merge_with_builtin(self):
        """测试自定义模板覆盖内置模板"""
        custom_config = {
            "custom_templates": {
                "tdd": {
                    "stages": [
                        {
                            "id": "parse",
                            "timeout": 600,  # 覆盖超时
                        }
                    ]
                }
            }
        }
        template = resolve_template("tdd", custom_config)
        # 找到 parse 阶段并验证超时被覆盖
        parse_stage = next((s for s in template["stages"] if s["id"] == "parse"), None)
        assert parse_stage is not None
        assert parse_stage["timeout"] == 600

    def test_custom_stages_add_new_stage(self):
        """测试自定义模板添加新阶段"""
        custom_config = {
            "custom_templates": {
                "tdd": {
                    "stages": [
                        {
                            "id": "extra_step",
                            "name": "额外步骤",
                            "auto": True,
                            "command": "echo 'extra'",
                            "timeout": 120,
                        }
                    ]
                }
            }
        }
        template = resolve_template("tdd", custom_config)
        # 原始 12 个 + 1 个新 = 13
        assert len(template["stages"]) == 13
        extra = next((s for s in template["stages"] if s["id"] == "extra_step"), None)
        assert extra is not None
        assert extra["name"] == "额外步骤"


class TestLoadProjectConfig:
    """测试项目配置加载"""

    def test_nonexistent_path_returns_empty(self):
        config = load_project_config("/nonexistent/path")
        assert config == {}

    def test_path_without_config_returns_empty(self):
        config = load_project_config("/tmp")
        assert config == {}
