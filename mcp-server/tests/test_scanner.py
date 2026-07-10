"""项目扫描器单元测试"""
import sys
import tempfile
from pathlib import Path

SRC = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, SRC)

from opspulse_mcp.project.scanner import (
    scan_project,
    detect_ci_backend,
    detect_languages,
    scan_modules,
    scan_configs,
    parse_pom_deps,
    generate_opspulse_yaml,
    init_project,
)


class TestDetectCI:
    """测试 CI 后端检测"""

    def test_github_actions(self, tmp_path):
        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "test.yml").write_text("on: push")
        result = detect_ci_backend(tmp_path)
        assert result.startswith("github-actions:")

    def test_jenkins(self, tmp_path):
        (tmp_path / "Jenkinsfile").write_text("pipeline {}")
        result = detect_ci_backend(tmp_path)
        assert result == "jenkins"

    def test_gitlab_ci(self, tmp_path):
        (tmp_path / ".gitlab-ci.yml").write_text("stages:")
        result = detect_ci_backend(tmp_path)
        assert result == "gitlab-ci"

    def test_harness(self, tmp_path):
        harness_dir = tmp_path / "harness"
        harness_dir.mkdir()
        result = detect_ci_backend(tmp_path)
        assert result == "harness"

    def test_unknown(self, tmp_path):
        result = detect_ci_backend(tmp_path)
        assert result == "unknown"


class TestDetectLanguages:
    """测试语言检测"""

    def test_python_project(self, tmp_path):
        for i in range(5):
            (tmp_path / f"test_{i}.py").write_text("# code")
        langs = detect_languages(tmp_path)
        assert "python" in langs

    def test_java_project(self, tmp_path):
        for i in range(5):
            (tmp_path / f"Test_{i}.java").write_text("// code")
        langs = detect_languages(tmp_path)
        assert "java" in langs

    def test_mixed_project(self, tmp_path):
        for i in range(5):
            (tmp_path / f"test_{i}.py").write_text("# code")
        for i in range(5):
            (tmp_path / f"test_{i}.java").write_text("// code")
        langs = detect_languages(tmp_path)
        assert "python" in langs
        assert "java" in langs

    def test_below_threshold(self, tmp_path):
        (tmp_path / "test.py").write_text("# code")
        (tmp_path / "test2.py").write_text("# code")
        langs = detect_languages(tmp_path)
        assert "python" not in langs


class TestScanModules:
    """测试模块扫描"""

    def test_maven_modules(self, tmp_path):
        pom = tmp_path / "pom.xml"
        pom.write_text("<project><modules><module>mod1</module></modules></project>")
        modules = scan_modules(tmp_path)
        assert "mod1" in modules

    def test_npm_workspaces(self, tmp_path):
        pkg = tmp_path / "package.json"
        pkg.write_text('{"workspaces": {"packages": ["packages/*"]}}')
        pkgs_dir = tmp_path / "packages"
        pkgs_dir.mkdir()
        (pkgs_dir / "pkg1").mkdir()
        modules = scan_modules(tmp_path)
        assert len(modules) > 0

    def test_subdir_with_build_files(self, tmp_path):
        sub = tmp_path / "service-a"
        sub.mkdir()
        (sub / "pom.xml").write_text("<project/>")
        modules = scan_modules(tmp_path)
        assert "service-a" in modules


class TestScanConfigs:
    """测试配置扫描"""

    def test_dockerfile(self, tmp_path):
        (tmp_path / "Dockerfile").write_text("FROM python")
        configs = scan_configs(tmp_path)
        assert any(c["type"] == "docker" for c in configs)

    def test_application_yml(self, tmp_path):
        (tmp_path / "application.yml").write_text("server:")
        configs = scan_configs(tmp_path)
        assert any(c["type"] == "spring-config" for c in configs)

    def test_nginx_conf(self, tmp_path):
        (tmp_path / "nginx.conf").write_text("server {}")
        configs = scan_configs(tmp_path)
        assert any(c["type"] == "nginx" for c in configs)


class TestParsePomDeps:
    """测试 POM 依赖解析"""

    def test_basic_deps(self, tmp_path):
        pom = tmp_path / "pom.xml"
        pom.write_text("""
        <project>
            <dependencies>
                <dependency><artifactId>spring-boot</artifactId></dependency>
                <dependency><artifactId>junit</artifactId></dependency>
            </dependencies>
        </project>
        """)
        deps = parse_pom_deps(pom)
        assert "spring-boot" in deps
        assert "junit" in deps

    def test_no_deps(self, tmp_path):
        pom = tmp_path / "pom.xml"
        pom.write_text("<project/>")
        deps = parse_pom_deps(pom)
        assert deps == []


class TestGenerateYaml:
    """测试 YAML 生成"""

    def test_github_actions_config(self):
        info = {
            "name": "test-project",
            "modules": [],
            "languages": ["python"],
            "ci_backend": "github-actions:cicd.yml",
            "configs": [],
            "pom_dependencies": [],
        }
        yaml_content = generate_opspulse_yaml(info)
        assert "test-project" in yaml_content
        assert "github-actions" in yaml_content
        assert "python" in yaml_content

    def test_jenkins_config(self):
        info = {
            "name": "test-project",
            "modules": [],
            "languages": ["java"],
            "ci_backend": "jenkins",
            "configs": [],
            "pom_dependencies": [],
        }
        yaml_content = generate_opspulse_yaml(info)
        assert "jenkins" in yaml_content


class TestInitProject:
    """测试项目初始化"""

    def test_init_creates_config(self, tmp_path):
        result = init_project(str(tmp_path))
        assert result["ok"] is True
        config_file = tmp_path / ".opspulse.yaml"
        assert config_file.exists()

    def test_init_existing_without_force(self, tmp_path):
        init_project(str(tmp_path))
        result = init_project(str(tmp_path))
        assert result["ok"] is False
        assert "已存在" in result["error"]

    def test_init_with_force_overwrites(self, tmp_path):
        init_project(str(tmp_path))
        result = init_project(str(tmp_path), force=True)
        assert result["ok"] is True

    def test_init_returns_project_info(self, tmp_path):
        # 创建一些测试文件
        (tmp_path / "test.py").write_text("# code")
        (tmp_path / "test2.py").write_text("# code")
        (tmp_path / "test3.py").write_text("# code")
        
        result = init_project(str(tmp_path))
        assert result["ok"] is True
        info = result["project_info"]
        assert info["name"] == tmp_path.name
        assert "python" in info["languages"]
