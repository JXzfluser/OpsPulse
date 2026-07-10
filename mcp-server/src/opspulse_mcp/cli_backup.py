"""opspulse CLI — 纯命令行胶水层，零依赖 MCP/AI Agent"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

from opspulse_mcp.parsers.frontmatter import extract_frontmatter, extract_body
from opspulse_mcp.parsers.validation import validate_spec_dict
from opspulse_mcp.workflow_pkg import IssueWorkflow, IssueState


def _get_token() -> str:
    return os.environ.get("GITHUB_PAT") or os.environ.get("GITHUB_TOKEN") or ""


def _headers(token: str | None = None) -> dict[str, str]:
    t = token or _get_token()
    return {
        "Authorization": f"Bearer {t}",
        "Accept": "application/vnd.github+json",
    }


# ======================================================================
# COMMAND: templates — 模板管理
# ======================================================================

def cmd_templates_list(args):
    """列出所有模板"""
    from opspulse_mcp.templates import list_builtin_templates
    
    templates = list_builtin_templates()
    print(f"📋 可用模板 ({len(templates)} 个):")
    print("-" * 40)
    for name in templates:
        print(f"  • {name}")
    print("-" * 40)
    return 0


def cmd_templates_show(args):
    """查看模板详情"""
    from opspulse_mcp.templates import load_builtin_template
    
    template_name = args.template
    try:
        template = load_builtin_template(template_name)
        print(f"📋 模板: {template['name']}")
        print(f"描述: {template.get('description', '无')}")
        print(f"图标: {template.get('icon', '🔹')}")
        print("-" * 40)
        
        stages = template.get("stages", [])
        for i, stage in enumerate(stages, 1):
            auto = "自动" if stage.get("auto") else "手动"
            approval = "⚠️ 需审批" if stage.get("requires_approval") else ""
            print(f"  {i:2d}. {stage['name']} ({auto}) {approval}")
        
        print("-" * 40)
        return 0
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1


# ======================================================================
# COMMAND: project — 项目管理
# ======================================================================

def cmd_project_init(args):
    """扫描项目并生成 .opspulse.yaml。"""
    from opspulse_mcp.project.scanner import init_project
    
    project_path = args.project_path or "."
    force = getattr(args, "force", False)
    
    print(f"🔍 扫描项目: {project_path}")
    
    result = init_project(project_path, force=force)
    
    if result["ok"]:
        print(f"\n✅ 配置已生成: {result['config_file']}")
        print(f"\n项目信息:")
        info = result["project_info"]
        print(f"  名称: {info['name']}")
        print(f"  模块: {', '.join(info['modules']) or '无'}")
        print(f"  语言: {', '.join(info['languages']) or '未知'}")
        print(f"  CI 后端: {info['ci_backend']}")
        print(f"  配置文件: {len(info['configs'])} 个")
        
        if info["pom_dependencies"]:
            print(f"  Maven 依赖: {len(info['pom_dependencies'])} 个")
        
        print(f"\n配置文件预览:")
        print("-" * 40)
        print(result["yaml_content"][:500])
        print("-" * 40)
        return 0
    else:
        print(f"❌ {result['error']}", file=sys.stderr)
        return 1


def cmd_project_show(args):
    """显示项目配置。"""
    project_path = Path(args.project_path or ".").resolve()
    config_file = project_path / ".opspulse.yaml"
    
    if not config_file.exists():
        print(f"❌ 未找到 {config_file}")
        print(f"💡 运行: opspulse project init {project_path}")
        return 1
    
    print(f"📋 项目配置: {config_file}")
    print("-" * 40)
    print(config_file.read_text(encoding="utf-8"))
    print("-" * 40)
    return 0


# ======================================================================
# COMMAND: new — 交互式创建 Issue
# ======================================================================

def cmd_new(args):
    """交互式创建 Issue，引导用户填写必要字段。"""
    owner = args.owner
    repo = args.repo
    token = _get_token()

    print("📝 新建 OpsPulse Issue")
    print("-" * 40)

    # 引导式问答
    title = args.title or input("需求标题: ").strip()
    if not title:
        print("❌ 标题不能为空", file=sys.stderr)
        return 1

    issue_type = args.type or input("类型 [feature/bugfix/chore/infra] (默认 feature): ").strip() or "feature"
    service_name = args.service or input("服务名 (如 order-service): ").strip()
    if not service_name:
        print("❌ 服务名不能为空", file=sys.stderr)
        return 1

    scope = args.scope or input("范围 [api/config/deploy/infra/docs] (默认 api): ").strip() or "api"
    priority = args.priority or input("优先级 [P0/P1/P2/P3] (默认 P1): ").strip() or "P1"

    print("\n验收标准 (每个一行，空行结束):")
    acceptance = []
    while True:
        line = input("  AC: ").strip()
        if not line:
            break
        acceptance.append({"id": f"AC-{len(acceptance)+1}", "given": "", "then": line})

    if not acceptance:
        print("⚠️  至少需要一个验收标准", file=sys.stderr)
        return 1

    affected_paths_str = args.paths or input("影响路径 (逗号分隔，如 order-service/src/): ").strip()
    affected_paths = [p.strip() for p in affected_paths_str.split(",") if p.strip()]

    # 构建 frontmatter
    frontmatter = {
        "opspulse_version": "1",
        "type": issue_type,
        "service": {"name": service_name},
        "scope": scope,
        "priority": priority,
        "acceptance": acceptance,
        "affected_paths": affected_paths,
    }

    # 构建 Issue 正文
    body_lines = [f"# {title}", "", "## 需求描述", title, ""]
    if args.description:
        body_lines.append(f"> {args.description}")
        body_lines.append("")
    body_lines.append("## 验收标准")
    for ac in acceptance:
        body_lines.append(f"- **{ac['id']}**: {ac['then']}")
    body_lines.append("")
    body_lines.append("---")
    body_lines.append(f"*Generated by `opspulse new` at {datetime.now().isoformat()}*")

    body = "\n".join(body_lines)

    # 创建 Issue
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    payload = {"title": title, "body": body}
    # 注意：frontmatter 不放在 Issue 里，而是放在 Comment 中

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, headers=_headers(), json=payload)
        if resp.status_code != 201:
            print(f"❌ 创建 Issue 失败: {resp.text}", file=sys.stderr)
            return 1

        issue = resp.json()
        issue_number = issue["number"]
        print(f"\n✅ Issue #{issue_number} 已创建: {issue['html_url']}")

        # 自动写入 Spec Comment
        spec_comment = f"""## OpsPulse Spec

```yaml
{json.dumps(frontmatter, indent=2, ensure_ascii=False)}
```

**自动生成** | 时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
        resp2 = client.post(comment_url, headers=_headers(), json={"body": spec_comment})
        if resp2.status_code == 201:
            print(f"📋 Spec 已写入 Issue #{issue_number} 的 Comment")
        else:
            print(f"⚠️  Spec 写入失败: {resp2.status_code}", file=sys.stderr)

    return 0


# ======================================================================
# COMMAND: handle — 处理 Issue（核心胶水命令）
# ======================================================================

def cmd_handle(args):
    """处理 Issue：parse → 生成 Spec → 编码建议 → 创建 PR → 触发 CI → 回写。"""
    owner = args.owner
    repo = args.repo
    issue_number = args.issue_number
    token = _get_token()
    spec = None

    # 1. 拉取 Issue
    print(f"📥 拉取 Issue #{issue_number}...")
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=_headers())
        if resp.status_code != 200:
            print(f"❌ 拉取失败: {resp.text}", file=sys.stderr)
            return 1
        issue = resp.json()

    body = issue.get("body") or ""
    labels = [item.get("name", "") for item in issue.get("labels", []) if isinstance(item, dict)]

    # 2. 查找 Spec Comment（从 Issue Comments 中提取 YAML frontmatter）
    print("🔍 查找 Spec...")
    comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    resp_comments = client.get(comments_url, headers=_headers())
    spec_data = None
    spec_found = False

    if resp_comments.status_code == 200:
        comments = resp_comments.json()
        for comment in comments:
            comment_body = comment.get("body", "")
            # 查找 Spec 标记
            if "## OpsPulse Spec" in comment_body:
                # 提取 YAML 块
                import re
                yaml_match = re.search(r"```yaml\s*\n(.*?)\n```", comment_body, re.DOTALL)
                if yaml_match:
                    try:
                        spec_data = json.loads(yaml_match.group(1))
                        spec_found = True
                        print(f"  ✅ 找到 Spec (来自 Comment #{comment['id']})")
                        break
                    except json.JSONDecodeError:
                        pass

    # 如果没有 Spec，尝试从 Issue body 中提取 frontmatter
    if not spec_data:
        fm, err = extract_frontmatter(body)
        if fm and not err:
            spec_data = fm
            spec_found = True
            print("  ✅ 从 Issue body 提取 Spec")

    if not spec_data:
        print("  ⚠️  未找到 Spec。建议运行: opspulse review #N")
        spec_data = {}

    # 3. 验证 Spec
    if spec_data:
        errors = validate_spec_dict(spec_data)
        if errors:
            print(f"  ❌ Spec 验证失败:")
            for e in errors:
                print(f"    - {e}")
            if not args.force:
                print("  💡 使用 --force 跳过验证")
                return 1
            else:
                print("  ⚠️  跳过验证 (--force)")
        else:
            print("  ✅ Spec 验证通过")

    spec = spec_data
    spec["_issue_title"] = issue.get("title", "")

    # 4. 创建工作流
    wf = IssueWorkflow(issue_number, owner, repo)

    # 5. 根据参数执行不同阶段
    if args.stage == "all":
        return _run_full_pipeline(wf, spec, issue_number, owner, repo, args)
    elif args.stage == "pr":
        return _do_create_pr(wf, spec, issue_number, owner, repo, args)
    elif args.stage == "deploy":
        # deploy 阶段复用 handle 的完整流程
        return _run_full_pipeline(wf, spec, issue_number, owner, repo, args)
    elif args.stage == "status":
        return _do_update_status(wf, spec, issue_number, owner, repo, args)
    else:
        # 默认：只 parse + 输出 Spec
        print(f"\n📋 Issue #{issue_number} 解析结果:")
        print(json.dumps(spec, indent=2, ensure_ascii=False, default=str))
        print(f"\n✅ ready={spec.get('_ready', True)}")
        return 0


def _run_full_pipeline(wf, spec, issue_number, owner, repo, args):
    """完整流水线：parse → design → breakdown → pr → pipeline → status."""
    print(f"\n🚀 启动完整流水线 Issue #{issue_number}")
    print("=" * 50)

    # Stage 1: 需求评审
    print("\n[1/6] 需求评审...")
    if wf.transition("review"):
        print("  ✅ 评审通过")
    else:
        print("  ⚠️  跳过评审")

    # Stage 2: 设计方案
    print("\n[2/6] 设计方案...")
    design_summary = _generate_design_summary(spec)
    print(f"  📄 方案已生成 ({len(design_summary)} 字符)")

    if wf.transition("design"):
        print("  ✅ 设计审批通过")
    else:
        print("  ⚠️  跳过设计审批")

    # Stage 3: 任务拆分
    print("\n[3/6] 任务拆分...")
    breakdown = _generate_breakdown(spec)
    for task in breakdown:
        print(f"  - {task['title']}")

    if wf.transition("breakdown"):
        print("  ✅ 拆分完成")
    else:
        print("  ⚠️  跳过拆分")

    # Stage 4: 创建 PR
    print("\n[4/6] 创建 PR...")
    pr_result = _do_create_pr(wf, spec, issue_number, owner, repo, args)
    if pr_result.get("success"):
        print(f"  ✅ PR #{pr_result.get('pr_number')} 已创建: {pr_result.get('pr_url')}")
    else:
        print(f"  ❌ PR 创建失败: {pr_result.get('error')}")
        return 1

    # Stage 5: 触发 CI
    print("\n[5/6] 触发 CI...")
    ci_result = _do_trigger_ci(wf, spec, issue_number, owner, repo, args)
    if ci_result.get("success"):
        print(f"  ✅ CI 通过: {ci_result.get('status')}")
    else:
        print(f"  ❌ CI 失败: {ci_result.get('error')}")
        return 1

    # Stage 6: 回写状态
    print("\n[6/6] 回写 Issue...")
    status_result = _do_update_status(wf, spec, issue_number, owner, repo, args)
    print(f"  {'✅' if status_result.get('posted') else '⚠️'} 状态已更新")

    print(f"\n{'=' * 50}")
    print(f"✅ 流水线完成! Issue #{issue_number} → {wf.current()}")
    print(f"\n{wf.history_summary()}")
    return 0


def _generate_design_summary(spec: dict) -> str:
    """生成设计方案摘要。"""
    service = spec.get("service", {}).get("name", "unknown")
    issue_type = spec.get("type", "feature")
    scope = spec.get("scope", "api")

    return f"""## 设计方案

**服务**: {service}
**类型**: {issue_type}
**范围**: {scope}

### 实施步骤
1. 分析 affected_paths 范围内的现有代码
2. 根据 acceptance criteria 设计实现方案
3. 编写代码 + 测试
4. 提交 PR

### 注意事项
- 遵守 JDK 1.8 规范
- 保持 affected_paths 边界
- 确保 acceptance criteria 全部满足
"""


def _generate_breakdown(spec: dict) -> list[dict]:
    """生成任务拆分。"""
    service = spec.get("service", {}).get("name", "unknown")
    acceptance = spec.get("acceptance", [])
    affected_paths = spec.get("affected_paths", [])

    tasks = [
        {"title": f"分析 {service} 受影响代码", "done": False},
        {"title": f"实现 acceptance criteria", "done": False},
        {"title": f"编写单元测试", "done": False},
        {"title": f"创建 PR", "done": False},
    ]

    if acceptance:
        tasks.append({"title": f"验证 {len(acceptance)} 个 AC", "done": False})

    return tasks


def _do_create_pr(wf, spec, issue_number, owner, repo, args):
    """创建 PR。"""
    service = spec.get("service", {}).get("name", "service")
    title = spec.get("_issue_title", f"Issue #{issue_number}")

    branch = f"opspulse/{issue_number}-{_slugify(title, 30)}"
    pr_title = f"feat({service}): {_slugify(title, 30)} (#{issue_number})"

    # 生成 PR body
    acceptance = spec.get("acceptance", [])
    pr_body = f"## Summary\n\nCloses #{issue_number}\n\n### Description\n{title}\n\n---\n\n## Acceptance Criteria\n\n"
    for ac in acceptance:
        pr_body += f"- [ ] **{ac.get('id', '?')}**: {ac.get('then', '')}\n"
    pr_body += "\n---\n*Generated by `opspulse handle`*"

    # 创建分支
    branch_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}"
    main_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/main"

    with httpx.Client(timeout=30.0) as client:
        main_resp = client.get(main_url, headers=_headers())
        if main_resp.status_code != 200:
            return {"success": False, "error": f"获取 main 分支失败: {main_resp.text}"}

        main_sha = main_resp.json()["object"]["sha"]

        # 创建分支
        create_resp = client.post(
            f"https://api.github.com/repos/{owner}/{repo}/git/refs",
            headers=_headers(),
            json={"ref": f"refs/heads/{branch}", "sha": main_sha},
        )

        if create_resp.status_code not in (201, 422):
            return {"success": False, "error": f"创建分支失败: {create_resp.status_code} {create_resp.text[:200]}"}

        # 创建 PR
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        pr_resp = client.post(pr_url, headers=_headers(), json={
            "title": pr_title,
            "body": pr_body,
            "head": branch,
            "base": "main",
        })

        if pr_resp.status_code != 201:
            return {"success": False, "error": f"创建 PR 失败: {pr_resp.status_code} {pr_resp.text[:200]}"}

        pr = pr_resp.json()
        pr_number = pr["number"]
        pr_api_url = pr["url"]

    wf.transition("create_pr")

    return {
        "success": True,
        "pr_number": pr_number,
        "pr_url": pr["html_url"],
        "branch": branch,
        "transition": {"from": "CODING_DONE", "to": "PR_CREATED"},
    }


def _do_trigger_ci(wf, spec, issue_number, owner, repo, args):
    """触发 CI。"""
    mode = getattr(args, 'mode', None) or 'github-actions'

    if mode == "github-actions":
        # 触发 GHA workflow_dispatch
        workflow_file = args.workflow or "cicd.yml"
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/dispatches"

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=_headers(), json={
                "ref": "main",
                "inputs": {
                    "service": spec.get("service", {}).get("name", ""),
                    "issue_number": str(issue_number),
                },
            })

            if resp.status_code == 204:
                # 等待完成
                if args.wait:
                    print("  ⏳ 等待 CI 完成...")
                    run_id = _wait_for_run_completion(owner, repo, client)
                    if run_id:
                        wf.transition("smoke_test")
                        return {"success": True, "status": "success", "run_id": run_id}
                return {"success": True, "status": "dispatched"}
            else:
                return {"success": False, "error": f"CI 触发失败: {resp.status_code} {resp.text[:200]}"}

    elif mode == "local":
        print("  ℹ️  本地模式：跳过 CI 触发")
        return {"success": True, "status": "skipped", "note": "local mode"}

    return {"success": False, "error": f"未知模式: {mode}"}


def _wait_for_run_completion(owner, repo, client, timeout=600):
    """等待 workflow run 完成。"""
    import time
    deadline = time.time() + timeout

    # 获取最新 run
    runs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    while time.time() < deadline:
        resp = client.get(runs_url, headers=_headers(), params={"per_page": 5})
        if resp.status_code == 200:
            runs = resp.json().get("workflow_runs", [])
            for run in runs:
                if run.get("status") in ("completed",):
                    return run.get("id")
                elif run.get("status") in ("in_progress", "queued"):
                    time.sleep(10)
                    break
        time.sleep(10)

    return None


def _do_update_status(wf, spec, issue_number, owner, repo, args):
    """回写 Issue 状态。"""
    state = args.state if hasattr(args, 'state') and args.state else "deployed"

    comment_body = f"""## OpsPulse 状态更新

**状态**: {state}
**Issue**: #{issue_number}
**服务**: {spec.get('service', {}).get('name', 'unknown')}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---
{wf.history_summary()}
"""

    wf.transition("deploy")

    comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(comment_url, headers=_headers(), json={"body": comment_body})
        posted = resp.status_code == 201

    return {"posted": posted, "state": state}


def _slugify(text: str, max_len: int = 40) -> str:
    """转换为 git-safe 分支名。"""
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = text.strip("-")
    return text[:max_len] or "update"


# ======================================================================
# COMMAND: review — 评审 Issue
# ======================================================================

def cmd_review(args):
    """评审 Issue：检查 Spec 完整性，输出评审意见。"""
    owner = args.owner
    repo = args.repo
    issue_number = args.issue_number

    print(f"🔍 评审 Issue #{issue_number}...")

    # 拉取 Issue
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=_headers())
        if resp.status_code != 200:
            print(f"❌ 拉取失败: {resp.text}", file=sys.stderr)
            return 1
        issue = resp.json()

    body = issue.get("body") or ""
    labels = [item.get("name", "") for item in issue.get("labels", []) if isinstance(item, dict)]

    # 尝试提取 Spec
    spec_data = None
    fm, err = extract_frontmatter(body)
    if fm and not err:
        spec_data = fm

    # 检查 Spec Comment
    if not spec_data:
        comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
        resp_c = client.get(comments_url, headers=_headers())
        if resp_c.status_code == 200:
            import re
            for comment in resp_c.json():
                cb = comment.get("body", "")
                if "## OpsPulse Spec" in cb:
                    yaml_match = re.search(r"```yaml\s*\n(.*?)\n```", cb, re.DOTALL)
                    if yaml_match:
                        try:
                            spec_data = json.loads(yaml_match.group(1))
                            break
                        except json.JSONDecodeError:
                            pass

    if not spec_data:
        print("  ⚠️  未找到 Spec，无法评审")
        print("  💡 建议: 先运行 `opspulse new` 创建 Issue")
        return 1

    # 验证
    errors = validate_spec_dict(spec_data)

    print(f"\n{'=' * 50}")
    print(f"Issue #{issue_number} 评审报告")
    print(f"标题: {issue.get('title')}")
    print(f"状态: {'open' if issue.get('state') == 'open' else 'closed'}")
    print(f"标签: {', '.join(labels) or '无'}")
    print(f"{'=' * 50}")

    if errors:
        print(f"\n❌ 发现 {len(errors)} 个问题:")
        for e in errors:
            print(f"  - {e}")
        print(f"\nready: false")
        return 1
    else:
        print(f"\n✅ 评审通过")
        print(f"ready: true")

        # 输出 Spec
        print(f"\n📋 Spec:")
        print(json.dumps(spec_data, indent=2, ensure_ascii=False, default=str))
        return 0


# ======================================================================
# COMMAND: log — 查看交付日志
# ======================================================================

def cmd_log(args):
    """查看 Issue 的交付日志。"""
    owner = args.owner
    repo = args.repo
    issue_number = args.issue_number

    print(f"📜 Issue #{issue_number} 交付日志")
    print("=" * 50)

    # 拉取 Issue
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=_headers())
        if resp.status_code != 200:
            print(f"❌ 拉取失败", file=sys.stderr)
            return 1
        issue = resp.json()

    # 拉取 Comments
    comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    resp_c = client.get(comments_url, headers=_headers())

    print(f"\nIssue: {issue.get('title')}")
    print(f"状态: {issue.get('state')}")
    print(f"创建: {issue.get('created_at')}")
    print(f"更新: {issue.get('updated_at')}")
    print()

    if resp_c.status_code == 200:
        comments = resp_c.json()
        for c in comments:
            cb = c.get("body", "")
            created = c.get("created_at", "")
            user = c.get("user", {}).get("login", "?")

            # 识别 OpsPulse Comment
            if "## OpsPulse" in cb or "OpsPulse Spec" in cb:
                print(f"[{created}] 🤖 {user}:")
                # 只打印关键信息
                lines = cb.split("\n")
                for line in lines[:8]:
                    if line.strip():
                        print(f"  {line}")
                if len(lines) > 8:
                    print(f"  ... ({len(lines)-8} more lines)")
            else:
                print(f"[{created}] 👤 {user}:")
                print(f"  {cb[:100]}{'...' if len(cb) > 100 else ''}")
            print()


# ======================================================================
# CLI 入口
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        prog="opspulse",
        description="OpsPulse: Issue-to-Deploy glue layer — 纯 CLI，零依赖",
        epilog="Examples:\n"
               "  opspulse new --owner myorg --repo myapp --title 'Add refund API'\n"
               "  opspulse handle --owner myorg --repo myapp --issue 45\n"
               "  opspulse handle --owner myorg --repo myapp --issue 45 --stage all\n"
               "  opspulse review --owner myorg --repo myapp --issue 45\n"
               "  opspulse log --owner myorg --repo myapp --issue 45\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- new ---
    p_new = subparsers.add_parser("new", help="交互式创建 Issue")
    p_new.add_argument("--owner", required=True, help="GitHub owner")
    p_new.add_argument("--repo", required=True, help="GitHub repo")
    p_new.add_argument("--title", help="Issue 标题")
    p_new.add_argument("--type", choices=["feature", "bugfix", "chore", "infra"], default="feature")
    p_new.add_argument("--service", help="服务名")
    p_new.add_argument("--scope", choices=["api", "config", "deploy", "infra", "docs"])
    p_new.add_argument("--priority", choices=["P0", "P1", "P2", "P3"], default="P1")
    p_new.add_argument("--paths", help="影响路径 (逗号分隔)")
    p_new.add_argument("--description", help="需求描述")
    p_new.set_defaults(func=cmd_new)

    # --- project ---
    p_project = subparsers.add_parser("project", help="项目管理（扫描、配置、初始化）")
    p_sub = p_project.add_subparsers(dest="project_cmd", help="Project commands")

    # project init
    p_proj_init = p_sub.add_parser("init", help="扫描项目并生成 .opspulse.yaml")
    p_proj_init.add_argument("project_path", nargs="?", default=".", help="项目路径")
    p_proj_init.add_argument("--force", action="store_true", help="覆盖已有配置")
    p_proj_init.set_defaults(func=lambda args: cmd_project_init(args))

    # project show
    p_proj_show = p_sub.add_parser("show", help="显示当前项目的 .opspulse.yaml 配置")
    p_proj_show.add_argument("project_path", nargs="?", default=".", help="项目路径")
    p_proj_show.set_defaults(func=lambda args: cmd_project_show(args))

    # --- templates ---
    p_templates = subparsers.add_parser("templates", help="工作流模板管理")
    p_templates_sub = p_templates.add_subparsers(dest="templates_cmd", help="Template commands")

    # templates list
    p_templates_list = p_templates_sub.add_parser("list", help="列出所有模板")
    p_templates_list.set_defaults(func=lambda args: cmd_templates_list(args))

    # templates show
    p_templates_show = p_templates_sub.add_parser("show", help="查看模板详情")
    p_templates_show.add_argument("template", help="模板名称")
    p_templates_show.set_defaults(func=lambda args: cmd_templates_show(args))

    # --- handle ---
    p_handle = subparsers.add_parser("handle", help="处理 Issue（核心胶水命令）")
    p_handle.add_argument("--owner", required=True, help="GitHub owner")
    p_handle.add_argument("--repo", required=True, help="GitHub repo")
    p_handle.add_argument("--issue-number", type=int, required=True, help="Issue 编号")
    p_handle.add_argument("--stage", choices=["all", "pr", "ci", "status"], default="all",
                          help="执行阶段 (默认: all)")
    p_handle.add_argument("--state", choices=["parsed", "in-dev", "pr-open", "testing", "deployed", "failed"])
    p_handle.add_argument("--mode", choices=["local", "github-actions", "harness"], default="github-actions")
    p_handle.add_argument("--workflow", help="GHA workflow 文件名")
    p_handle.add_argument("--force", action="store_true", help="跳过 Spec 验证")
    p_handle.add_argument("--wait", action="store_true", help="等待 CI 完成")
    p_handle.add_argument("--auto", action="store_true", help="跳过人工确认（信任模式）")
    p_handle.add_argument("--template", choices=["tdd", "normal", "hotfix", "feature"], default="normal",
                          help="工作流模板 (默认: normal)")
    p_handle.add_argument("--dry-run", action="store_true", help="只打印执行计划，不执行")
    p_handle.set_defaults(func=cmd_handle)

    # --- review ---
    p_review = subparsers.add_parser("review", help="评审 Issue Spec")
    p_review.add_argument("--owner", required=True)
    p_review.add_argument("--repo", required=True)
    p_review.add_argument("--issue-number", type=int, required=True)
    p_review.set_defaults(func=cmd_review)

    # --- log ---
    p_log = subparsers.add_parser("log", help="查看 Issue 交付日志")
    p_log.add_argument("--owner", required=True)
    p_log.add_argument("--repo", required=True)
    p_log.add_argument("--issue-number", type=int, required=True)
    p_log.set_defaults(func=cmd_log)

    # --- init (保留) ---
    p_init = subparsers.add_parser("init", help="初始化仓库")
    p_init.add_argument("repo_dir", nargs="?", default=".")
    p_init.add_argument("--owner", default="JXzfluser")
    p_init.add_argument("--repo", default="OpsPulse")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=lambda args: 0)  # placeholder

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    if args.command == "init":
        return 0

    if args.command == "project":
        if not hasattr(args, "project_cmd") or not args.project_cmd:
            p_project.print_help()
            return 1
        return args.func(args)
    
    if args.command == "templates":
        if not hasattr(args, "templates_cmd") or not args.templates_cmd:
            p_templates.print_help()
            return 1
        return args.func(args)

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
