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


VERSION = 2
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


def iter_state_files():
    if not STATE_ROOT.exists():
        return []
    return sorted(STATE_ROOT.glob("*/tasks.json"))


def load_state_file(path):
    try:
        with path.open("r", encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(state, dict) or not isinstance(state.get("tasks"), dict):
        return None
    return state


def find_task_context(current_root):
    current_root = current_root.resolve()
    for state_path in iter_state_files():
        state = load_state_file(state_path)
        if not state:
            continue
        repo = state.get("repo")
        if not repo:
            continue
        for name, task in state["tasks"].items():
            worktree = task.get("worktree")
            if worktree and Path(worktree).resolve() == current_root:
                return Path(repo).resolve(), name, task
    return None, None, None


def repo_context():
    current_root = repo_root()
    task_repo, task_name, task = find_task_context(current_root)
    if task_repo:
        return task_repo, current_root, task_name, task
    return current_root, current_root, None, None


def require_main_project_dir():
    current_root = repo_root()
    task_repo, task_name, _task = find_task_context(current_root)
    if task_repo:
        raise WorktreeError(
            "该操作必须在主项目目录执行。\n"
            f"当前目录是任务 worktree: {task_name}\n"
            f"主项目目录: {task_repo}"
        )
    return current_root


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
                    "preview": None,
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
    if state.get("version") == 1 and isinstance(state.get("tasks"), dict):
        state["version"] = VERSION
        state.setdefault("preview", None)
        save_state(root, state)
    if state.get("version") != VERSION or not isinstance(state.get("tasks"), dict):
        raise WorktreeError(f"状态文件格式不兼容: {state_path}")
    state.setdefault("preview", None)
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


def head_tree(root):
    return text(["git", "rev-parse", "HEAD^{tree}"], root)


def main_status(root):
    return run(["git", "status", "--porcelain"], root).stdout.decode(errors="replace").rstrip("\n")


def has_staged_changes(status):
    return any(line and line[0] not in (" ", "?") for line in status.splitlines())


def require_clean_main(root):
    status = main_status(root)
    if status:
        raise WorktreeError(
            "主项目目录存在未提交改动，已停止。\n"
            "请先手动确认、提交或清理后再执行该操作。\n\n"
            f"{status}"
        )


def validate_task_name(name):
    if not name:
        raise WorktreeError("任务名不能为空")
    if name.startswith("-"):
        raise WorktreeError("任务名不能以 '-' 开头，避免和 --all、--clear 等命令选项冲突。")


def tree_from_worktree(path):
    with tempfile.NamedTemporaryFile(prefix="codex-worktree-index-") as index_file:
        index_file.close()
        env = {"GIT_INDEX_FILE": index_file.name}
        run(["git", "read-tree", "HEAD"], path, env=env)
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


def clear_preview_if_safe(root, state, *, required=False):
    preview = state.get("preview")
    if not preview:
        if required:
            require_clean_main(root)
            print("当前没有已记录的 switch 预览状态，主项目目录已是干净状态。")
        return False

    current_tree = tree_from_worktree(root)
    preview_tree = preview.get("tree")
    status = main_status(root)
    if current_tree != preview_tree:
        if status:
            raise WorktreeError(
                "主项目目录存在未提交改动，但这些改动不等于上一次 switch 记录的预览状态，已停止。\n"
                "请先手动确认、提交或清理这些改动。\n\n"
                f"{status}"
            )
        state["preview"] = None
        return False
    if has_staged_changes(status):
        raise WorktreeError(
            "主项目目录存在已暂存改动，虽然内容等于 switch 预览状态，但工具不会自动清理已暂存内容。\n"
            "请先手动提交、取消暂存或清理后再继续。\n\n"
            f"{status}"
        )

    target_tree = head_tree(root)
    restore_patch = diff_trees(root, current_tree, target_tree)
    result = apply_patch_to_repo(root, root, restore_patch, "switch-clear")
    state["preview"] = None
    if result == "empty":
        print("已清除 switch 预览记录，主项目目录已是当前 HEAD。")
    else:
        print(f"已清除 switch 预览并恢复主项目目录到当前 HEAD。恢复方式: {result}")
    return True


def clear_stale_preview_if_clean(root, state):
    if state.get("preview") and not main_status(root):
        state["preview"] = None
        return True
    return False


def sync_one_task(root, state, name):
    task = get_task(state, name)
    task_path = Path(task["worktree"])
    if not task_path.exists():
        raise WorktreeError(f"任务目录不存在: {task_path}")

    base_tree = task["base_tree"]
    task_tree = tree_from_worktree(task_path)
    main_tree = head_tree(root)

    if task_tree == main_tree:
        task["base_tree"] = main_tree
        task["status"] = "active"
        task["last_synced_at"] = now()
        task["updated_at"] = now()
        return "already-current"

    main_update_patch = diff_trees(root, base_tree, main_tree)
    if patch_is_empty(main_update_patch):
        task["base_tree"] = main_tree
        task["status"] = "active"
        task["last_synced_at"] = now()
        task["updated_at"] = now()
        return "empty"

    result = apply_patch_to_repo(root, task_path, main_update_patch, f"{task['slug']}-sync")
    task["base_tree"] = main_tree
    task["status"] = "active"
    task["last_synced_at"] = now()
    task["updated_at"] = now()
    return result


def sync_conflict_advice(name):
    return (
        f"任务同步遇到冲突，已停止: {name}\n"
        "建议处理方式:\n"
        f"1. 先在任务 worktree 中继续处理该任务，完成后执行 $worktree-merge {name}。\n"
        "2. 让 Codex 根据保存的补丁和冲突文件，手动把主线变化合入任务 worktree。\n"
        "3. 如果该任务不再需要，清理任务后从最新主线重新创建。"
    )


def get_task(state, name):
    task = state["tasks"].get(name)
    if not task:
        raise WorktreeError(f"未找到任务: {name}")
    return task


def cmd_new(args):
    root = require_main_project_dir()
    require_clean_main(root)
    state = load_state(root)
    name = args.name.strip()
    validate_task_name(name)
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
    base_tree = head_tree(root)
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
    root, _current_root, _task_name, _task = repo_context()
    state = load_state(root)
    if clear_stale_preview_if_clean(root, state):
        save_state(root, state)
    tasks = state["tasks"]
    print(f"仓库: {root}")
    print(f"状态目录: {repo_state_dir(root)}")
    preview = state.get("preview")
    if preview:
        print(f"当前 switch 预览: {preview.get('task')}")
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
    root = require_main_project_dir()
    state = load_state(root)
    preview_cleared = clear_preview_if_safe(root, state)
    require_clean_main(root)
    task = get_task(state, args.name.strip())
    task_path = Path(task["worktree"])
    if not task_path.exists():
        raise WorktreeError(f"任务目录不存在: {task_path}")

    base_tree = task["base_tree"]
    task_tree = tree_from_worktree(task_path)
    task_patch = diff_trees(root, base_tree, task_tree)
    if patch_is_empty(task_patch):
        if preview_cleared:
            save_state(root, state)
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
    state["preview"] = None
    save_state(root, state)

    print(f"已合并到主项目目录，主项目未自动 commit。应用方式: {result}")
    print(f"已反向同步到任务 worktree。同步方式: {sync_result}")
    print("请在主项目目录手动重启服务验证；验证通过后由你手动 commit。")


def cmd_sync(args):
    root = require_main_project_dir()
    require_clean_main(root)
    state = load_state(root)
    preview_cleared = clear_stale_preview_if_clean(root, state)

    if args.all:
        if args.name:
            raise WorktreeError("$worktree-sync --all 不能同时指定任务名。")
        synced = []
        failed = []
        for name in list(state["tasks"].keys()):
            try:
                result = sync_one_task(root, state, name)
                save_state(root, state)
                synced.append((name, result))
            except WorktreeError as exc:
                failed.append((name, str(exc)))

        if synced:
            print("已同步任务:")
            for name, result in synced:
                print(f"- {name}: {result}")
        else:
            print("没有任务完成同步。")
            if preview_cleared:
                save_state(root, state)

        if failed:
            print("以下任务同步被阻止:")
            for name, message in failed:
                print(f"- {name}")
                print(message)
                if "补丁无法自动应用" in message:
                    print(sync_conflict_advice(name))
        return

    name = (args.name or "").strip()
    validate_task_name(name)
    try:
        result = sync_one_task(root, state, name)
    except WorktreeError as exc:
        message = str(exc)
        if "补丁无法自动应用" in message:
            raise WorktreeError(f"{message}\n\n{sync_conflict_advice(name)}")
        raise
    save_state(root, state)
    print(f"已把主项目当前文件同步到任务 worktree。同步方式: {result}")


def sh_quote(value):
    return "'" + value.replace("'", "'\"'\"'") + "'"


def cmd_switch(args):
    root = require_main_project_dir()
    state = load_state(root)

    if args.clear:
        if args.name:
            raise WorktreeError("$worktree-switch --clear 不能同时指定任务名。")
        clear_preview_if_safe(root, state, required=True)
        save_state(root, state)
        return

    name = (args.name or "").strip()
    validate_task_name(name)
    clear_preview_if_safe(root, state)
    require_clean_main(root)

    task = get_task(state, name)
    task_path = Path(task["worktree"])
    if not task_path.exists():
        raise WorktreeError(f"任务目录不存在: {task_path}")

    base_tree = task["base_tree"]
    task_tree = tree_from_worktree(task_path)
    task_patch = diff_trees(root, base_tree, task_tree)
    if patch_is_empty(task_patch):
        state["preview"] = None
        save_state(root, state)
        print(f"任务没有可预览改动: {task['name']}")
        return

    print("待预览文件:")
    print(changed_files(root, base_tree, task_tree))
    result = apply_patch_to_repo(root, root, task_patch, f"{task['slug']}-switch")
    preview_tree = tree_from_worktree(root)
    state["preview"] = {
        "task": task["name"],
        "slug": task["slug"],
        "head": text(["git", "rev-parse", "HEAD"], root),
        "tree": preview_tree,
        "switched_at": now(),
    }
    save_state(root, state)

    print(f"已切换主项目目录到任务预览状态: {task['name']}")
    print(f"应用方式: {result}")
    print("该操作只用于临时验证；不会更新任务基线、不会反向同步、不会自动 commit。")


def cmd_current(_args):
    root, current_root, task_name, task = repo_context()
    state = load_state(root)
    if task_name:
        print(f"当前窗口位于任务 worktree: {task_name}")
        print(f"分支: {task['branch']}")
        print(f"主项目目录: {root}")
        print(f"任务目录: {task['worktree']}")
        return

    preview = state.get("preview")
    current_tree = tree_from_worktree(root)
    status = main_status(root)
    if preview and current_tree == preview.get("tree"):
        if not status and head_tree(root) == current_tree:
            state["preview"] = None
            save_state(root, state)
            print("当前主项目目录处于主线基线状态。")
            print(f"主项目目录: {current_root}")
            return
        print(f"当前主项目目录正在预览任务: {preview.get('task')}")
        print(f"主项目目录: {current_root}")
        return
    if status:
        print("当前主项目目录有未提交改动，不属于已记录的 switch 预览状态。")
        print(f"主项目目录: {current_root}")
        print(status)
        return
    if preview:
        state["preview"] = None
        save_state(root, state)
    print("当前主项目目录处于主线基线状态。")
    print(f"主项目目录: {current_root}")


def cmd_info(args):
    root, _current_root, _task_name, _task = repo_context()
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
    root = require_main_project_dir()
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
  current
  switch <name>
  switch --clear
  merge <name>
  sync <name>
  sync --all
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
    p.add_argument("name", nargs="?")
    p.add_argument("--all", action="store_true")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("switch")
    p.add_argument("name", nargs="?")
    p.add_argument("--clear", action="store_true")
    p.set_defaults(func=cmd_switch)

    p = sub.add_parser("current")
    p.set_defaults(func=cmd_current)

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
