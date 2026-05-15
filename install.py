#!/usr/bin/env python3
import shutil
from pathlib import Path


VERSION = "2"
BEGIN = "<!-- codex-worktree-rules:start -->"
END = "<!-- codex-worktree-rules:end -->"
SKILL_BUNDLE_NAME = "codex-cli-worktree"
COMMANDS = [
    "worktree-list",
    "worktree-new",
    "worktree-merge",
    "worktree-sync",
    "worktree-end",
    "worktree-resume",
    "worktree-help",
]

RULE_BLOCK = f"""{BEGIN}
## 通用 worktree 并行开发规则

版本：{VERSION}

- worktree 命令由用户级 Codex Skills 和脚本提供：
  - Skills：`~/.agents/skills/codex-cli-worktree/worktree-*/SKILL.md`
  - 脚本：`~/.agents/skills/codex-cli-worktree/scripts/worktree-task.py`
  - 状态：`~/.codex-cli-worktree/state/`
- 常用命令：
  - `$worktree-new 任务名`：在主项目目录创建独立 worktree 任务目录和任务分支。
  - `$worktree-merge 任务名`：把任务改动合并回主项目目录，不自动 commit，并把合并后的文件反向同步回任务 worktree。
  - `$worktree-sync 任务名`：把主项目当前文件同步到任务 worktree。
  - `$worktree-end 任务名`：清理任务 worktree、任务分支和本地状态记录。
  - `$worktree-list`：查看所有 worktree 任务。
  - `$worktree-resume 任务名`：新会话继续已有任务。
  - `$worktree-help`：查看命令帮助。
- `$worktree-new`、`$worktree-merge`、`$worktree-end` 必须在主项目目录执行；`$worktree-list`、`$worktree-sync`、`$worktree-resume` 建议在主项目目录执行。
- 主项目目录只用于合并、用户手动运行服务验证和用户手动 commit；任务 worktree 目录用于具体开发和测试。
- worktree 命令不得自动启动任何项目服务。
- `$worktree-merge` 不得自动 commit，合并成功后必须反向同步到任务 worktree。
- `$worktree-merge` 遇到无法自动应用的冲突时，必须停止，列出冲突文件和合理解决方案，由用户决定。
- 遇到业务冲突、数据库 schema、权限、路由、授权、配置、状态机冲突，必须先说明方案并询问用户。
- worktree 任务状态按仓库隔离保存在本地 `~/.codex-cli-worktree/state/`，不会提交到任何仓库。
{END}
"""


def copy_tree_files(src_dir, dst_dir, pattern):
    dst_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for src in sorted(src_dir.glob(pattern)):
        dst = dst_dir / src.name
        shutil.copy2(src, dst)
        copied.append(dst)
    return copied


def install_skill_bundle(source_root, target_bundle):
    source_skills = source_root / "skills" / SKILL_BUNDLE_NAME
    if not source_skills.is_dir():
        raise FileNotFoundError(f"缺少 skills 目录: {source_skills}")

    target_bundle.mkdir(parents=True, exist_ok=True)
    installed = []
    for command in COMMANDS:
        src = source_skills / command
        dst = target_bundle / command
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        installed.append(dst / "SKILL.md")

    scripts_dst = target_bundle / "scripts"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    installed_scripts = copy_tree_files(source_root / "scripts", scripts_dst, "worktree-*.py")
    return installed, installed_scripts


def cleanup_legacy_install(home_codex):
    removed = 0
    legacy_prompts = home_codex / "prompts"
    if legacy_prompts.is_dir():
        for path in legacy_prompts.glob("worktree-*.md"):
            path.unlink()
            removed += 1

    legacy_script = home_codex / "scripts" / "worktree-task.py"
    if legacy_script.exists():
        legacy_script.unlink()
        removed += 1
    return removed


def update_agents(home_codex):
    agents = home_codex / "AGENTS.md"
    content = agents.read_text(encoding="utf-8") if agents.exists() else ""

    if BEGIN in content and END in content:
        before, rest = content.split(BEGIN, 1)
        _old, after = rest.split(END, 1)
        new_content = before.rstrip() + "\n\n" + RULE_BLOCK + after.lstrip()
        changed = new_content != content
    else:
        sep = "\n\n" if content.strip() else ""
        new_content = content.rstrip() + sep + RULE_BLOCK + "\n"
        changed = True

    if changed:
        agents.write_text(new_content, encoding="utf-8")
        return "updated"
    return "unchanged"


def main():
    source_root = Path(__file__).resolve().parent
    home_codex = Path.home() / ".codex"
    home_agents = Path.home() / ".agents"
    target_bundle = home_agents / "skills" / SKILL_BUNDLE_NAME
    tool_state = Path.home() / ".codex-cli-worktree" / "state"
    home_codex.mkdir(parents=True, exist_ok=True)
    home_agents.mkdir(parents=True, exist_ok=True)

    skills, scripts = install_skill_bundle(source_root, target_bundle)
    legacy_removed = cleanup_legacy_install(home_codex)
    agents_status = update_agents(home_codex)
    tool_state.mkdir(parents=True, exist_ok=True)

    print("worktree Skills 已安装/更新。")
    print(f"skills: {len(skills)} 个 -> {target_bundle}")
    print(f"scripts: {len(scripts)} 个 -> {target_bundle / 'scripts'}")
    print(f"legacy cleanup: {legacy_removed} 个旧文件")
    print(f"AGENTS.md: {agents_status} -> {home_codex / 'AGENTS.md'}")
    print(f"state: {tool_state}")
    print("请重启 Codex CLI，让 Skills 生效。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
