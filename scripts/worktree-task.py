#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


VERSION = 1
STATE_ROOT = Path.home() / ".codex-cli-worktree" / "state"


class WorktreeError(Exception):
    pass


def run(args, cwd, check=True, env=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise WorktreeError(
            f"命令失败: {' '.join(args)}\n"
            f"stdout:\n{proc.stdout.decode(errors='replace')}\n"
            f"stderr:\n{proc.stderr.decode(errors='replace')}"
        )
    return proc


def text(args, cwd, check=True, env=None):
    proc = run(args, cwd, check=check, env=env)
    return proc.stdout.decode(errors="replace").strip()


def repo_root():
    return Path(text(["git", "rev-parse", "--show-toplevel"], Path.cwd())).resolve()


def repo_state_id(root):
    digest = hashlib.sha1(str(root).encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", root.name).strip("-").lower() or "repo"
    return f"{slug}-{digest}"


def repo_state_dir(root):
    return STATE_ROOT / repo_state_id(root)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_state(root):
    state_path = repo_state_dir(root) / "tasks.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if not state_path.exists():
        state_path.write_text(
            json.dumps(
                {
                    "version": VERSION,
                    "repo": str(root),
                    "repo_id": repo_state_id(root),
                    "tasks": {},
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return state_path


def load_state(root):
    state_path = ensure_state(root)
    with state_path.open("r", encoding="utf-8") as f:
        state = json.load(f)
    if state.get("version") != VERSION or not isinstance(state.get("tasks"), dict):
        raise WorktreeError(f"状态文件格式不兼容: {state_path}")
    return state


def save_state(root, state):
    state_path = ensure_state(root)
    tmp = state_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(state_path)


def slugify(name):
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    if not slug:
        slug = "task"
    slug = slug[:40].strip("-") or "task"
    return f"{slug}-{digest}"


def require_clean_main(root):
    status = text(["git", "status", "--porcelain"], root)
    if status:
        raise WorktreeError(
            "主项目目录存在未提交改动，已停止。\n"
            "请先手动确认、提交或清理后再执行该操作。\n\n"
            f"{status}"
        )


def tree_from_worktree(path):
    with tempfile.NamedTemporaryFile(prefix="codex-worktree-index-") as index_file:
        index_file.close()
        env = {"GIT_INDEX_FILE": index_file.name}
        run(["git", "read-tree", "--empty"], path, env=env)
        run(["git", "add", "-A", "--", "."], path, env=env)
        return text(["git", "write-tree"], path, env=env)


def diff_trees(root, old_tree, new_tree):
    return run(["git", "diff", "--binary", old_tree, new_tree], root).stdout


def changed_files(root, old_tree, new_tree):
    output = text(["git", "diff", "--name-status", old_tree, new_tree], root)
    return output or "(无文件变化)"


def patch_is_empty(patch):
    return not patch.strip()


def save_patch(root, slug, patch):
    patch_dir = repo_state_dir(root) / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    patch_path = patch_dir / f"{slug}-{stamp}.patch"
    patch_path.write_bytes(patch)
    return patch_path


def apply_patch_to_repo(root, target, patch, slug):
    if patch_is_empty(patch):
        return "empty"

    patch_path = save_patch(root, slug, patch)
    direct_check = run(
        ["git", "apply", "--check", "--whitespace=nowarn", str(patch_path)],
        target,
        check=False,
    )
    if direct_check.returncode == 0:
        run(["git", "apply", "--whitespace=nowarn", str(patch_path)], target)
        return "applied"

    three_way_check = run(
        ["git", "apply", "--3way", "--check", "--whitespace=nowarn", str(patch_path)],
        target,
        check=False,
    )
    if three_way_check.returncode == 0:
        run(["git", "apply", "--3way", "--whitespace=nowarn", str(patch_path)], target)
        return "applied-3way"

    stderr = three_way_check.stderr.decode(errors="replace").strip()
    raise WorktreeError(
        "补丁无法自动应用，已停止且未改动目标目录。\n"
        f"补丁已保存: {patch_path}\n"
        "请让 Codex 根据补丁和当前文件分析冲突方案后再决定。\n\n"
        f"{stderr}"
    )


def get_task(state, name):
    task = state["tasks"].get(name)
    if not task:
        raise WorktreeError(f"未找到任务: {name}")
    return task


def cmd_new(args):
    root = repo_root()
    require_clean_main(root)
    state = load_state(root)
    name = args.name.strip()
    if not name:
        raise WorktreeError("任务名不能为空")
    if name in state["tasks"]:
        raise WorktreeError(f"任务已存在: {name}")

    slug = slugify(name)
    repo_name = root.name
    base_dir = root.parent / f"{repo_name}.worktrees"
    worktree = (base_dir / slug).resolve()
    branch = f"worktree/{slug}"
    if worktree.exists():
        raise WorktreeError(f"任务目录已存在: {worktree}")
    existing_branches = text(["git", "branch", "--list", branch], root)
    if existing_branches:
        raise WorktreeError(f"任务分支已存在: {branch}")

    base_dir.mkdir(parents=True, exist_ok=True)
    run(["git", "worktree", "add", "-b", branch, str(worktree), "HEAD"], root)
    base_tree = text(["git", "rev-parse", "HEAD^{tree}"], root)
    state["tasks"][name] = {
        "name": name,
        "slug": slug,
        "branch": branch,
        "worktree": str(worktree),
        "base_tree": base_tree,
        "status": "active",
        "created_at": now(),
        "updated_at": now(),
        "last_merged_at": None,
        "last_synced_at": now(),
    }
    save_state(root, state)
    print(f"已创建 worktree 任务: {name}")
    print(f"分支: {branch}")
    print(f"目录: {worktree}")
    print("继续开发命令:")
    print(f"cd {sh_quote(str(worktree))} && codex")
    print("请在该目录中打开新的 Codex CLI 继续开发；不要启动项目服务。")


def cmd_list(_args):
    root = repo_root()
    state = load_state(root)
    tasks = state["tasks"]
    print(f"仓库: {root}")
    print(f"状态目录: {repo_state_dir(root)}")
    if not tasks:
        print("当前没有 worktree 任务。")
        return
    for name, task in tasks.items():
        path = Path(task["worktree"])
        exists = "存在" if path.exists() else "缺失"
        dirty = "未知"
        if path.exists():
            base_tree = task.get("base_tree")
            current_tree = tree_from_worktree(path)
            dirty = "有未合并改动" if not patch_is_empty(diff_trees(root, base_tree, current_tree)) else "干净"
        print(f"- {name}")
        print(f"  状态: {task.get('status', 'unknown')} / {dirty} / 目录{exists}")
        print(f"  分支: {task['branch']}")
        print(f"  目录: {task['worktree']}")
        print(f"  更新时间: {task.get('updated_at')}")


def cmd_merge(args):
    root = repo_root()
    require_clean_main(root)
    state = load_state(root)
    task = get_task(state, args.name.strip())
    task_path = Path(task["worktree"])
    if not task_path.exists():
        raise WorktreeError(f"任务目录不存在: {task_path}")

    base_tree = task["base_tree"]
    task_tree = tree_from_worktree(task_path)
    task_patch = diff_trees(root, base_tree, task_tree)
    if patch_is_empty(task_patch):
        print(f"任务没有待合并改动: {task['name']}")
        return

    print("待合并文件:")
    print(changed_files(root, base_tree, task_tree))
    result = apply_patch_to_repo(root, root, task_patch, task["slug"])
    main_tree = tree_from_worktree(root)

    sync_patch = diff_trees(root, task_tree, main_tree)
    sync_result = apply_patch_to_repo(root, task_path, sync_patch, f"{task['slug']}-sync")

    task["base_tree"] = main_tree
    task["status"] = "merged-to-main-pending-user-commit"
    task["last_merged_at"] = now()
    task["last_synced_at"] = now()
    task["updated_at"] = now()
    save_state(root, state)

    print(f"已合并到主项目目录，主项目未自动 commit。应用方式: {result}")
    print(f"已反向同步到任务 worktree。同步方式: {sync_result}")
    print("请在主项目目录手动重启服务验证；验证通过后由你手动 commit。")


def cmd_sync(args):
    root = repo_root()
    state = load_state(root)
    task = get_task(state, args.name.strip())
    task_path = Path(task["worktree"])
    if not task_path.exists():
        raise WorktreeError(f"任务目录不存在: {task_path}")

    base_tree = task["base_tree"]
    task_tree = tree_from_worktree(task_path)
    task_delta = diff_trees(root, base_tree, task_tree)
    if not patch_is_empty(task_delta) and not args.force:
        print("任务 worktree 存在未合并改动，已停止同步。")
        print("未合并文件:")
        print(changed_files(root, base_tree, task_tree))
        print("请先执行 $worktree-merge，或确认放弃这些改动后让 Codex 使用 --force。")
        return

    main_tree = tree_from_worktree(root)
    sync_patch = diff_trees(root, task_tree, main_tree)
    result = apply_patch_to_repo(root, task_path, sync_patch, f"{task['slug']}-sync")
    task["base_tree"] = main_tree
    task["status"] = "active"
    task["last_synced_at"] = now()
    task["updated_at"] = now()
    save_state(root, state)
    print(f"已把主项目当前文件同步到任务 worktree。同步方式: {result}")


def sh_quote(value):
    return "'" + value.replace("'", "'\"'\"'") + "'"


def cmd_info(args):
    root = repo_root()
    state = load_state(root)
    task = get_task(state, args.name.strip())
    print(f"任务: {task['name']}")
    print(f"状态: {task.get('status', 'unknown')}")
    print(f"分支: {task['branch']}")
    print(f"目录: {task['worktree']}")
    print("继续开发命令:")
    print(f"cd {sh_quote(task['worktree'])} && codex")
    print("请在该目录中打开新的 Codex CLI 继续开发；不要启动项目服务。")


def cmd_end(args):
    root = repo_root()
    state = load_state(root)
    name = args.name.strip()
    task = get_task(state, name)
    task_path = Path(task["worktree"])
    if task_path.exists():
        base_tree = task["base_tree"]
        current_tree = tree_from_worktree(task_path)
        delta = diff_trees(root, base_tree, current_tree)
        if not patch_is_empty(delta) and not args.force:
            print("任务 worktree 还有未合并改动，已停止清理。")
            print("未合并文件:")
            print(changed_files(root, base_tree, current_tree))
            print("请先执行 $worktree-merge，或确认放弃后让 Codex 使用 --force。")
            return
        run(["git", "worktree", "remove", "--force", str(task_path)], root)

    branch_exists = text(["git", "branch", "--list", task["branch"]], root)
    if branch_exists:
        run(["git", "branch", "-D", task["branch"]], root)

    del state["tasks"][name]
    save_state(root, state)
    print(f"已清理 worktree 任务: {name}")


def cmd_help(_args):
    print(
        """codex-cli-worktree helper

Internal subcommands:
  new <name>
  list
  info <name>
  merge <name>
  sync <name>
  end <name>
  help

User-facing help is provided by the $worktree-help skill."""
    )


def build_parser():
    parser = argparse.ArgumentParser(description="Codex worktree task helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("new")
    p.add_argument("name")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("merge")
    p.add_argument("name")
    p.set_defaults(func=cmd_merge)

    p = sub.add_parser("sync")
    p.add_argument("name")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("end")
    p.add_argument("name")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_end)

    p = sub.add_parser("list")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("info")
    p.add_argument("name")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("help")
    p.set_defaults(func=cmd_help)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except WorktreeError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("已取消。", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
