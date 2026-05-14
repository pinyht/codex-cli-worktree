#!/usr/bin/env python3
import shutil
from pathlib import Path


VERSION = "1"
BEGIN = "<!-- codex-worktree-rules:start -->"
END = "<!-- codex-worktree-rules:end -->"

RULE_BLOCK = f"""{BEGIN}
## 通用 worktree 并行开发规则

版本：{VERSION}

- 自定义 worktree 命令由 `~/.codex/prompts/worktree-*.md` 和 `~/.codex/scripts/worktree-task.py` 提供。
- 常用命令：
  - `/worktree-new 任务名`：在主项目目录创建独立 worktree 任务目录和任务分支。
  - `/worktree-merge 任务名`：把任务改动合并回主项目目录，不自动 commit，并把合并后的文件反向同步回任务 worktree。
  - `/worktree-sync 任务名`：把主项目当前文件同步到任务 worktree。
  - `/worktree-end 任务名`：清理任务 worktree、任务分支和本地状态记录。
  - `/worktree-list`：查看所有 worktree 任务。
  - `/worktree-resume 任务名`：新会话继续已有任务。
- `/worktree-new`、`/worktree-merge`、`/worktree-end` 必须在主项目目录执行；`/worktree-list`、`/worktree-sync`、`/worktree-resume` 建议在主项目目录执行。
- 主项目目录只用于合并、用户手动运行服务验证和用户手动 commit；任务 worktree 目录用于具体开发和测试。
- worktree 命令不得自动启动任何项目服务。
- `/worktree-merge` 不得自动 commit，合并成功后必须反向同步到任务 worktree。
- `/worktree-merge` 遇到无法自动应用的冲突时，必须停止，列出冲突文件和合理解决方案，由用户决定。
- 遇到业务冲突、数据库 schema、权限、路由、授权、配置、状态机冲突，必须先说明方案并询问用户。
- worktree 任务状态按仓库隔离保存在本地 `~/.codex/worktree-state/`，不会提交到任何仓库。
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
    home_codex.mkdir(parents=True, exist_ok=True)

    prompts = copy_tree_files(source_root / "prompts", home_codex / "prompts", "worktree-*.md")
    scripts = copy_tree_files(source_root / "scripts", home_codex / "scripts", "worktree-*.py")
    agents_status = update_agents(home_codex)
    (home_codex / "worktree-state" / "patches").mkdir(parents=True, exist_ok=True)
    state_file = home_codex / "worktree-state" / "tasks.json"
    if not state_file.exists():
        state_file.write_text('{\n  "version": 1,\n  "tasks": {}\n}\n', encoding="utf-8")

    print("worktree 命令已安装/更新到 HOME 级 Codex 目录。")
    print(f"prompts: {len(prompts)} 个 -> {home_codex / 'prompts'}")
    print(f"scripts: {len(scripts)} 个 -> {home_codex / 'scripts'}")
    print(f"AGENTS.md: {agents_status} -> {home_codex / 'AGENTS.md'}")
    print(f"state: {home_codex / 'worktree-state'}")
    print("请重启 Codex CLI，让自定义斜杠命令生效。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
