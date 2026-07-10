"""扫描项目结构，自动生成 .opspulse.yaml 配置文件"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


def scan_project(project_path: str | Path) -> dict[str, Any]:
    """扫描项目，返回项目信息。"""
    path = Path(project_path)
    
    info = {
        "name": path.name,
        "path": str(path.resolve()),
        "modules": [],
        "ci_backend": detect_ci_backend(path),
        "languages": detect_languages(path),
        "configs": [],
        "pom_dependencies": [],
    }
    
    # 扫描模块
    info["modules"] = scan_modules(path)
    
    # 扫描配置文件
    info["configs"] = scan_configs(path)
    
    # 扫描 pom.xml 依赖
    pom_files = list(path.rglob("pom.xml"))
    if pom_files:
        for pom in pom_files[:5]:  # 最多扫描 5 个
            info["pom_dependencies"].extend(parse_pom_deps(pom))
    
    return info


def detect_ci_backend(path: Path) -> str:
    """检测 CI 后端。"""
    if (path / ".github" / "workflows").exists():
        # 找出可用的 workflow 文件
        workflows = list((path / ".github" / "workflows").glob("*.yml"))
        if workflows:
            return f"github-actions:{workflows[0].name}"
    
    if (path / "Jenkinsfile").exists():
        return "jenkins"
    
    if (path / ".gitlab-ci.yml").exists():
        return "gitlab-ci"
    
    if (path / "harness").exists():
        return "harness"
    
    return "unknown"


def detect_languages(path: Path) -> list[str]:
    """检测编程语言。"""
    languages = []
    ext_lang = {
        ".java": "java",
        ".kt": "kotlin",
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".rs": "rust",
    }
    
    ext_counts = {}
    for f in path.rglob("*"):
        if f.is_file() and f.suffix in ext_lang:
            lang = ext_lang[f.suffix]
            ext_counts[lang] = ext_counts.get(lang, 0) + 1
    
    for lang, count in sorted(ext_counts.items(), key=lambda x: -x[1]):
        if count >= 3:  # 至少 3 个文件才算一个模块
            languages.append(lang)
    
    return languages


def scan_modules(path: Path) -> list[str]:
    """扫描模块/子项目。"""
    modules = []
    
    # Maven 多模块
    pom_file = path / "pom.xml"
    if pom_file.exists():
        content = pom_file.read_text()
        # 提取 <module>xxx</module>
        module_matches = re.findall(r"<module>([^<]+)</module>", content)
        if module_matches:
            modules.extend(module_matches)
    
    # npm monorepo
    if (path / "package.json").exists():
        try:
            pkg = json.loads((path / "package.json").read_text())
            if "workspaces" in pkg:
                ws = pkg["workspaces"]
                if isinstance(ws, dict) and "packages" in ws:
                    for pattern in ws["packages"]:
                        modules.extend([str(p) for p in path.glob(pattern)])
        except json.JSONDecodeError:
            pass
    
    # 如果有子目录且包含构建文件，也算模块
    if not modules:
        for subdir in path.iterdir():
            if subdir.is_dir() and (
                (subdir / "pom.xml").exists() or
                (subdir / "package.json").exists() or
                (subdir / "Cargo.toml").exists() or
                (subdir / "build.gradle").exists()
            ):
                modules.append(subdir.name)
    
    return modules


def scan_configs(path: Path) -> list[dict[str, str]]:
    """扫描配置文件。"""
    configs = []
    config_patterns = {
        "application.yml": "spring-config",
        "application.yaml": "spring-config",
        "application.properties": "spring-config",
        "Dockerfile": "docker",
        "docker-compose.yml": "docker-compose",
        "nginx.conf": "nginx",
        ".env": "env",
    }
    
    for filename, config_type in config_patterns.items():
        found = list(path.rglob(filename))
        if found:
            for f in found[:5]:
                rel = str(f.relative_to(path))
                configs.append({"type": config_type, "path": rel})
    
    return configs


def parse_pom_deps(pom_path: Path) -> list[str]:
    """解析 pom.xml 中的依赖。"""
    try:
        content = pom_path.read_text()
        deps = re.findall(r"<artifactId>([^<]+)</artifactId>", content)
        return list(set(deps))[:20]  # 最多 20 个
    except Exception:
        return []


def generate_opspulse_yaml(info: dict[str, Any]) -> str:
    """生成 .opspulse.yaml 内容。"""
    ci_backend = info.get("ci_backend", "unknown")
    backend_type = ci_backend.split(":")[0] if ":" in ci_backend else ci_backend
    
    yaml_lines = [
        "# OpsPulse 项目交付配置",
        "# 自动生成，勿手动编辑（使用 opspulse project edit 编辑）",
        "",
        "# 项目标识",
        "project:",
        f"  name: {info['name']}",
        f"  modules: {json.dumps(info['modules'], ensure_ascii=False)}",
        f"  languages: {json.dumps(info['languages'], ensure_ascii=False)}",
        "",
        "# CI 配置",
        "ci:",
        f"  backend: {backend_type}",
    ]
    
    if backend_type == "github-actions":
        workflow_file = ci_backend.split(":")[1] if ":" in ci_backend else "cicd.yml"
        yaml_lines.extend([
            f"  github-actions:",
            f"    workflow_file: .github/workflows/{workflow_file}",
            f"    dispatch_event: workflow_dispatch",
            f"    inputs:",
            f"      service: '{{{{ service }}}}'",
            f"      issue_number: '{{{{ issue_number }}}}'",
        ])
    elif backend_type == "jenkins":
        yaml_lines.extend([
            "  jenkins:",
            f"    url: http://jenkins.example.com",
            f"    job: {info['name']}-build",
        ])
    
    yaml_lines.extend([
        "",
        "# 部署配置",
        "deploy:",
        "  environments:",
        "    - name: dev",
        "      auto: true",
        "      health_check: http://localhost:8080/actuator/health",
        "    - name: staging",
        "      auto: false",
        "    - name: prod",
        "      auto: false",
        "      strategy: canary",
        "",
        "# 交付流程",
        "workflow:",
        "  stages:",
        "    - name: parse",
        "      auto: true",
        "    - name: pr",
        "      auto: false",
        "    - name: ci",
        "      auto: true",
        "    - name: deploy",
        "      auto: false",
    ])
    
    return "\n".join(yaml_lines)


def init_project(project_path: str | Path, force: bool = False) -> dict[str, Any]:
    """初始化项目，生成 .opspulse.yaml。"""
    path = Path(project_path).resolve()
    
    config_file = path / ".opspulse.yaml"
    if config_file.exists() and not force:
        return {
            "ok": False,
            "error": f"{config_file} 已存在，使用 --force 覆盖",
        }
    
    # 扫描项目
    info = scan_project(path)
    
    # 生成配置
    yaml_content = generate_opspulse_yaml(info)
    
    # 写入文件
    config_file.write_text(yaml_content, encoding="utf-8")
    
    return {
        "ok": True,
        "config_file": str(config_file),
        "project_info": info,
        "yaml_content": yaml_content,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python project/scanner.py <project_path>")
        sys.exit(1)
    
    result = init_project(sys.argv[1])
    if result["ok"]:
        print(f"✅ 配置已生成: {result['config_file']}")
        print(f"\n{result['yaml_content']}")
    else:
        print(f"❌ {result['error']}", file=sys.stderr)
        sys.exit(1)
