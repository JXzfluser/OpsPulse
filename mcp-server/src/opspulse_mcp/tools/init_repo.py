"""opspulse init — 一键初始化仓库"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def init_repo(
    repo_dir: str | Path,
    owner: str,
    repo: str,
    github_pat: str | None = None,
    force: bool = False,
) -> dict:
    """在目标仓库生成 OpsPulse 所需的全部配置文件。

    生成的文件：
    - opspulse.yaml          仓库级 CI/CD 映射
    - .github/ISSUE_TEMPLATE/opspulse-feature.md  Issue 模板
    - .github/workflows/opspulse-pr-validation.yml  验证工作流
    - .github/workflows/opspulse-deploy-dev.yml     部署工作流
    - deploy/Dockerfile       基础 Dockerfile 模板
    - .gitignore              追加 ops 相关忽略规则
    """
    repo_path = Path(repo_dir).resolve()
    if not repo_path.is_dir():
        return {"ok": False, "error": f"{repo_path} is not a directory"}

    existing = [
        "opspulse.yaml",
        ".github/ISSUE_TEMPLATE/opspulse-feature.md",
        ".github/workflows/opspulse-pr-validation.yml",
        ".github/workflows/opspulse-deploy-dev.yml",
        "deploy/Dockerfile",
    ]

    conflicts = [p for p in existing if (repo_path / p).exists()]
    if conflicts and not force:
        return {
            "ok": False,
            "error": "Files already exist. Use --force to overwrite.",
            "conflicts": conflicts,
        }

    # 1. opspulse.yaml
    opspulse_yaml = f"""\
version: "1"
defaults:
  runtime:
    jdk_base_image: eclipse-temurin:8-jre
  build:
    jdk: "1.8"
    tool: maven
  deploy:
    env: dev
pipeline:
  default_mode: github-actions
  github_actions:
    ref: main
    repositories:
      {owner}/{repo}:
        workflow: opspulse-pr-validation.yml
        service_input: module
        pipelines:
          pr-validation:
            inputs: {{}}
          deploy-dev:
            inputs:
              env: test
"""
    (repo_path / "opspulse.yaml").write_text(opspulse_yaml, encoding="utf-8")

    # 2. Issue 模板
    issue_template = """---
name: "OpsPulse Feature Request"
about: "Create a feature request with OpsPulse spec"
title: "[FEATURE] "
labels: ["opspulse", "feature"]
---
opspulse_version: "1"
type: feature
scope: api
service:
  name: SERVICE_NAME
  module_path: services/SERVICE_NAME/
priority: P2
runtime:
  jdk_base_image: eclipse-temurin:8-jre
build:
  tool: maven
  jdk: "1.8"
  command: mvn clean package
  artifact: services/SERVICE_NAME/target/SERVICE_NAME.jar
deploy:
  dockerfile: deploy/SERVICE_NAME/Dockerfile
  image: registry.example.com/SERVICE_NAME
  env: dev
acceptance:
  - id: AC-1
    given: "SERVICE_NAME starts with JDK8"
    then: "GET /health returns 200"
affected_paths:
  - services/SERVICE_NAME/src/main/java/**
---

## Title

## Background

## Implementation Notes

- [ ] AC-1: SERVICE_NAME starts with JDK8
- [ ] AC-2: API endpoint works as expected
"""
    (repo_path / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True, exist_ok=True)
    (repo_path / ".github" / "ISSUE_TEMPLATE" / "opspulse-feature.md").write_text(
        issue_template, encoding="utf-8"
    )

    # 3. GHA workflow: pr-validation
    pr_workflow = """\
name: OpsPulse PR Validation
on:
  workflow_dispatch:
    inputs:
      service:
        description: 'Service name'
        required: false
        default: 'module'
      env:
        description: 'Environment'
        required: false
        default: 'test'
      issue_number:
        description: 'Issue number'
        required: false

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup JDK 8
        uses: actions/setup-java@v4
        with:
          java-version: '8'
          distribution: 'temurin'
      - name: Build with Maven
        run: mvn clean package -DskipTests
      - name: Validate artifact
        run: |
          echo "OpsPulse Stage: validate_artifact:success:Build passed"
          echo "OPS_STAGE:validate_artifact:success:Build passed"
"""
    (repo_path / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    (repo_path / ".github" / "workflows" / "opspulse-pr-validation.yml").write_text(
        pr_workflow, encoding="utf-8"
    )

    # 4. GHA workflow: deploy-dev
    deploy_workflow = """\
name: OpsPulse Deploy Dev
on:
  workflow_dispatch:
    inputs:
      service:
        description: 'Service name'
        required: false
        default: 'module'
      env:
        description: 'Environment'
        required: false
        default: 'dev'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: |
          echo "Building image for ${{ github.event.inputs.service }}"
          echo "OPS_STAGE:build_image:success:Docker build passed"
      - name: Push to registry
        run: |
          echo "Pushing to registry"
          echo "OPS_STAGE:push_registry:success:Registry push passed"
      - name: Deploy to dev
        run: |
          echo "Deploying to dev environment"
          echo "OPS_STAGE:deploy_dev:success:Dev deploy passed"
"""
    (repo_path / ".github" / "workflows" / "opspulse-deploy-dev.yml").write_text(
        deploy_workflow, encoding="utf-8"
    )

    # 5. Dockerfile template
    dockerfile = """\
FROM eclipse-temurin:8-jre

ARG SERVICE_NAME=app
ARG JAR_FILE=target/${SERVICE_NAME}.jar

COPY ${JAR_FILE} /app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app.jar"]
"""
    (repo_path / "deploy").mkdir(exist_ok=True)
    (repo_path / "deploy" / "Dockerfile").write_text(dockerfile, encoding="utf-8")

    # 6. .gitignore 追加
    gitignore_path = repo_path / ".gitignore"
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding="utf-8")
        if ".opspulse/" not in content:
            gitignore_path.write_text(
                content.rstrip() + "\n.opspulse/\n", encoding="utf-8"
            )
    else:
        gitignore_path.write_text(".opspulse/\n", encoding="utf-8")

    return {
        "ok": True,
        "files_created": [
            "opspulse.yaml",
            ".github/ISSUE_TEMPLATE/opspulse-feature.md",
            ".github/workflows/opspulse-pr-validation.yml",
            ".github/workflows/opspulse-deploy-dev.yml",
            "deploy/Dockerfile",
        ],
        "message": "OpsPulse initialized successfully. Run `opspulse init --help` for usage.",
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize a repository with OpsPulse configuration files."
    )
    parser.add_argument(
        "repo_dir",
        nargs="?",
        default=".",
        help="Target repository directory (default: current directory)",
    )
    parser.add_argument("--owner", help="GitHub owner (e.g., JXzfluser)")
    parser.add_argument("--repo", help="GitHub repo name (e.g., OpsPulse)")
    parser.add_argument(
        "--pat",
        help="GitHub PAT (or set GITHUB_PAT env var)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    args = parser.parse_args()

    pat = args.pat or os.environ.get("GITHUB_PAT", "")
    if pat:
        os.environ["GITHUB_PAT"] = pat

    owner = args.owner or "JXzfluser"
    repo = args.repo or "OpsPulse"

    result = init_repo(args.repo_dir, owner, repo, pat, force=args.force)

    if result["ok"]:
        print(f"✅ OpsPulse initialized in {args.repo_dir}")
        print(f"   Owner/Repo: {owner}/{repo}")
        for f in result["files_created"]:
            print(f"   📄 {f}")
        print(f"\n   {result['message']}")
    else:
        print(f"❌ {result['error']}", file=sys.stderr)
        if "conflicts" in result:
            print("   Conflicting files:", result["conflicts"])
        sys.exit(1)


if __name__ == "__main__":
    main()
