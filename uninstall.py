#!/usr/bin/env python3
import shutil
from pathlib import Path


BEGIN = "<!-- codex-worktree-rules:start -->"
END = "<!-- codex-worktree-rules:end -->"
SKILL_BUNDLE_NAME = "codex-cli-worktree"


def remove_tree(path):
    if path.exists():
        shutil.rmtree(path)
        return "removed"
    return "not found"


def remove_agents_block(home_codex):
    agents = home_codex / "AGENTS.md"
    if not agents.exists():
        return "not found"

    content = agents.read_text(encoding="utf-8")
    if BEGIN not in content or END not in content:
        return "unchanged"

    before, rest = content.split(BEGIN, 1)
    _old, after = rest.split(END, 1)
    new_content = before.rstrip() + "\n\n" + after.lstrip()
    if new_content.strip():
        agents.write_text(new_content.rstrip() + "\n", encoding="utf-8")
    else:
        agents.write_text("", encoding="utf-8")
    return "updated"


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


def ask_keep_state():
    while True:
        answer = input("是否保留历史任务状态和补丁记录？[Y/n] ").strip().lower()
        if answer in ("", "y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("请输入 y 或 n。")


def main():
    home = Path.home()
    home_codex = home / ".codex"
    skill_bundle = home / ".agents" / "skills" / SKILL_BUNDLE_NAME
    tool_home = home / ".codex-cli-worktree"

    skills_status = remove_tree(skill_bundle)
    legacy_removed = cleanup_legacy_install(home_codex)
    agents_status = remove_agents_block(home_codex)

    keep_state = ask_keep_state()
    if keep_state:
        state_status = "kept"
    else:
        state_status = remove_tree(tool_home)

    print("codex-cli-worktree 已卸载。")
    print(f"skills: {skills_status} -> {skill_bundle}")
    print(f"legacy cleanup: {legacy_removed} 个旧文件")
    print(f"AGENTS.md: {agents_status} -> {home_codex / 'AGENTS.md'}")
    print(f"state: {state_status}")
    print("请重启 Codex CLI，让卸载结果生效。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
