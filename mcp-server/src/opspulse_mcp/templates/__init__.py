"""OpsPulse 工作流模板系统"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

BUILTIN_TEMPLATES_DIR = Path(__file__).parent / "builtin"


def list_builtin_templates() -> list[str]:
    """列出所有内置模板"""
    templates = []
    for f in BUILTIN_TEMPLATES_DIR.glob("*.yaml"):
        templates.append(f.stem)
    return sorted(templates)


def load_builtin_template(name: str) -> dict[str, Any]:
    """加载内置模板"""
    path = BUILTIN_TEMPLATES_DIR / f"{name}.yaml"
    if not path.exists():
        raise ValueError(f"内置模板 '{name}' 不存在")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_project_config(project_path: Optional[str] = None) -> dict[str, Any]:
    """加载项目配置"""
    if not project_path:
        return {}
    path = Path(project_path).resolve()
    config_file = path / ".opspulse.yaml"
    if not config_file.exists():
        return {}
    with config_file.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_template(template_name: str, project_config: Optional[dict] = None) -> dict[str, Any]:
    """解析模板：内置模板 + 项目级覆盖"""
    builtin = load_builtin_template(template_name)
    if not project_config:
        return builtin
    
    custom = project_config.get("custom_templates", {}).get(template_name)
    if custom:
        # 合并：custom 覆盖 builtin
        merged = builtin.copy()
        for key in custom:
            if key == "stages":
                base_stages = {s["id"]: s for s in merged.get("stages", [])}
                for stage in custom["stages"]:
                    base_stages[stage["id"]] = {**base_stages.get(stage["id"], {}), **stage}
                merged["stages"] = list(base_stages.values())
            else:
                merged[key] = custom[key]
        return merged
    return builtin
