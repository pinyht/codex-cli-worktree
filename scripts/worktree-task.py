#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


VERSION = 14
STATE_ROOT = Path.home() / ".codex-cli-worktree" / "state"


class WorktreeError(Exception):
    pass


def run(args, cwd, check=True, env=None, input_data=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        input=input_data,
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
    if state.get("version") in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13) and isinstance(state.get("tasks"), dict):
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


def branch_slug(name):
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    if not slug:
        slug = "task"
    slug = slug[:40].strip("-") or "task"
    return f"{slug}-{digest}"


def worktree_dir_name(name):
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    return f"task-{name}-{digest}"


def head_tree(root):
    return text(["git", "rev-parse", "HEAD^{tree}"], root)


def main_status(root):
    return run(["git", "status", "--porcelain"], root).stdout.decode(errors="replace").rstrip("\n")


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
    if name.endswith("-"):
        raise WorktreeError("任务名不能以 '-' 结尾，避免生成的 worktree 目录名出现连续分隔符。")
    if name in (".", ".."):
        raise WorktreeError("任务名不能是 '.' 或 '..'。")
    if len(name) > 80:
        raise WorktreeError("任务名不能超过 80 个字符。")
    if any(ch.isspace() for ch in name):
        raise WorktreeError("任务名不能包含空格、Tab 或换行，确保可直接复制到 $worktree-switch。")
    invalid = set('/\\:*?"<>|')
    bad_chars = sorted({ch for ch in name if ch in invalid or ord(ch) < 32})
    if bad_chars:
        chars = " ".join(repr(ch) for ch in bad_chars)
        raise WorktreeError(f"任务名包含不适合作为路径的字符: {chars}")


def tree_from_worktree(path):
    with tempfile.NamedTemporaryFile(prefix="codex-worktree-index-") as index_file:
        index_file.close()
        env = {"GIT_INDEX_FILE": index_file.name}
        run(["git", "read-tree", "HEAD"], path, env=env)
        run(["git", "add", "-A", "--", "."], path, env=env)
        return text(["git", "write-tree"], path, env=env)


def task_worktree_patch(task_path, task_tree):
    return run(
        ["git", "diff", "--binary", "--full-index", "HEAD", task_tree, "--"],
        task_path,
    ).stdout


def unmerged_files(root):
    return text(["git", "diff", "--name-only", "--diff-filter=U", "--"], root)


def git_stage_blob(root, stage, path):
    result = run(["git", "show", f":{stage}:{path}"], root, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.decode(errors="replace")


def conflict_marker_count(content):
    if content is None:
        return 0
    return sum(1 for line in content.splitlines() if line.startswith("<<<<<<< "))


def conflict_reason(path, ours, theirs):
    combined = f"{path}\n{ours or ''}\n{theirs or ''}".lower()
    path_lower = path.lower()
    reasons = []
    if path_lower.endswith((".md", ".txt", ".rst")) or "/docs/" in f"/{path_lower}":
        reasons.append("两边都修改了同一段文档内容")
    if any(word in combined for word in ("route", "router", "/api/", "path:", "httprouter", "handlefunc")):
        reasons.append("两边都修改了路由、页面入口或 API 注册区域")
    if any(word in combined for word in ("menu", "nav", "sidebar", "command", "settings", "配置", "入口")):
        reasons.append("两边都修改了菜单、命令入口或配置入口")
    if any(word in combined for word in ("schema", "migration", "permission", "auth", "state", "状态机", "权限", "授权")):
        reasons.append("包含 schema、权限、授权或状态机相关字样，需要确认语义")
    if not reasons:
        reasons.append("两边都修改了同一文本区域，Git 无法判断最终内容")
    return "；".join(dict.fromkeys(reasons))


def line_change_summary(base, ours, theirs):
    parts = []
    if base is None or ours is None:
        parts.append("主项目版本: 新增或删除文件")
    else:
        parts.append(f"主项目版本: {len(ours.splitlines())} 行")
    if base is None or theirs is None:
        parts.append("任务版本: 新增或删除文件")
    else:
        parts.append(f"任务版本: {len(theirs.splitlines())} 行")
    return "，".join(parts)


def short_changed_terms(base, content):
    if content is None:
        return []
    base_text = base or ""
    candidates = re.findall(
        r"(/[A-Za-z0-9_./:-]+|[A-Za-z_][A-Za-z0-9_./:-]{2,}|[\u4e00-\u9fff]{2,})",
        content,
    )
    seen = []
    for item in candidates:
        if item in base_text or item in seen:
            continue
        if len(item) > 48:
            item = item[:45] + "..."
        seen.append(item)
        if len(seen) >= 6:
            break
    return seen


def analyze_conflict_file(root, path):
    base = git_stage_blob(root, 1, path)
    ours = git_stage_blob(root, 2, path)
    theirs = git_stage_blob(root, 3, path)
    working = None
    try:
        working = (root / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    return {
        "path": path,
        "reason": conflict_reason(path, ours, theirs),
        "summary": line_change_summary(base, ours, theirs),
        "markers": conflict_marker_count(working),
        "ours_terms": short_changed_terms(base, ours),
        "theirs_terms": short_changed_terms(base, theirs),
    }


def format_conflict_analysis(root, conflicted_paths):
    lines = [f"检测到 {len(conflicted_paths)} 个冲突文件:"]
    for index, path in enumerate(conflicted_paths, 1):
        info = analyze_conflict_file(root, path)
        lines.append(f"\n{index}. {path}")
        lines.append(f"   冲突原因: {info['reason']}")
        lines.append(f"   改动规模: {info['summary']}")
        if info["markers"]:
            lines.append(f"   冲突块: {info['markers']} 个")
        if info["ours_terms"]:
            lines.append(f"   主项目侧关键词: {', '.join(info['ours_terms'])}")
        if info["theirs_terms"]:
            lines.append(f"   任务侧关键词: {', '.join(info['theirs_terms'])}")
        lines.append("   后续处理: 需要 Codex 读取冲突上下文后给出语义级修复方案")
    return "\n".join(lines)


def apply_task_patch(root, patch):
    result = run(["git", "apply", "--3way", "-"], root, check=False, input_data=patch)
    stdout = result.stdout.decode(errors="replace").strip()
    stderr = result.stderr.decode(errors="replace").strip()
    if result.returncode == 0:
        run(["git", "reset", "--"], root)
        return stdout, stderr

    conflicted = unmerged_files(root)
    conflicted_paths = conflicted.splitlines() if conflicted else []
    detail_parts = []
    if stdout:
        detail_parts.append(f"stdout:\n{stdout}")
    if stderr:
        detail_parts.append(f"stderr:\n{stderr}")
    detail = "\n".join(detail_parts).strip()
    if conflicted_paths:
        print(
            "任务改动与主项目当前提交存在合并冲突，已进入冲突处理引导。\n"
            "脚本不会自动 commit，也不会启动服务。"
        )
        if detail:
            print()
            print(detail)
        print()
        print(format_conflict_analysis(root, conflicted_paths))
        raise WorktreeError(
            "主项目目录已保留 Git 冲突状态，等待 Codex 进行 AI 语义分析和引导式处理。\n"
            "Codex 应读取冲突文件、base/主项目/任务三方版本，给出可选修复方案；"
            "用户选择后再修改文件解决冲突。"
        )
    raise WorktreeError(
        "任务改动无法三方合并到主项目目录，已停止。\n"
        "主项目目录可能保留了部分 Git apply 状态，请先查看 git status 后决定继续解决或手动清理。\n\n"
        f"{detail}"
    )


def task_changes_absorbed_by_main(root, task_path, changes):
    if not changes:
        return True
    task_tree = tree_from_worktree(task_path)
    task_head = text(["git", "rev-parse", "HEAD"], task_path)
    main_head = text(["git", "rev-parse", "HEAD"], root)
    result = run(
        ["git", "merge-tree", "--write-tree", "--merge-base", task_head, main_head, task_tree],
        root,
        check=False,
    )
    if result.returncode != 0:
        return False
    lines = result.stdout.decode(errors="replace").strip().splitlines()
    if not lines:
        return False
    merged_tree = lines[0]
    return merged_tree == head_tree(root)


def split_z(output):
    if not output:
        return []
    return output.decode(errors="replace").rstrip("\0").split("\0")


def validate_relative_path(path):
    rel = Path(path)
    if rel.is_absolute() or not path or ".." in rel.parts:
        raise WorktreeError(f"检测到不安全的 Git 路径，已停止: {path}")
    return path


def task_changes(task_path):
    conflicted = text(
        ["git", "diff", "--name-only", "--diff-filter=U", "HEAD", "--"],
        task_path,
    )
    if conflicted:
        raise WorktreeError(
            "任务 worktree 存在未解决冲突，已停止。\n"
            "请先在任务目录解决冲突后再切换或合并。\n\n"
            f"{conflicted}"
        )

    tokens = split_z(
        run(
            ["git", "diff", "--name-status", "-z", "--find-renames", "HEAD", "--"],
            task_path,
        ).stdout
    )
    changes = []
    i = 0
    while i < len(tokens):
        status = tokens[i]
        i += 1
        kind = status[:1]
        if kind in ("R", "C"):
            old_path = validate_relative_path(tokens[i])
            new_path = validate_relative_path(tokens[i + 1])
            i += 2
            if kind == "R":
                changes.append(("D", old_path))
            changes.append(("A", new_path))
            continue

        path = validate_relative_path(tokens[i])
        i += 1
        if kind == "D":
            changes.append(("D", path))
        else:
            changes.append((kind if kind in ("A", "M", "T") else "M", path))

    for path in split_z(run(["git", "ls-files", "--others", "--exclude-standard", "-z"], task_path).stdout):
        changes.append(("A", validate_relative_path(path)))

    return changes


def format_changes(changes):
    if not changes:
        return "(无文件变化)"
    return "\n".join(f"{status}\t{path}" for status, path in changes)


def change_map(changes):
    result = {}
    for status, path in changes:
        result[path] = status
    return result


def remove_path(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def copy_path(src_root, dst_root, rel_path):
    src = src_root / rel_path
    dst = dst_root / rel_path
    if not src.exists() and not src.is_symlink():
        raise WorktreeError(f"任务文件不存在，无法复制: {src}")
    if dst.exists() or dst.is_symlink():
        remove_path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir() and not src.is_symlink():
        shutil.copytree(src, dst, symlinks=True)
    else:
        shutil.copy2(src, dst, follow_symlinks=False)


def apply_task_files(task_path, target, changes):
    for status, rel_path in sorted(changes, key=lambda item: item[1], reverse=True):
        if status == "D":
            remove_path(target / rel_path)
    for status, rel_path in changes:
        if status != "D":
            copy_path(task_path, target, rel_path)


def reset_main_to_head(root):
    run(["git", "reset", "--hard", "HEAD"], root)
    run(["git", "clean", "-fd"], root)


def reset_task_to_commit(task_path, commit):
    run(["git", "reset", "--hard", commit], task_path)
    run(["git", "clean", "-fd"], task_path)


def reset_main_slot(root, state, *, required=False):
    preview = state.get("preview")
    status = main_status(root)
    if status:
        current_tree = tree_from_worktree(root)
        if preview and current_tree == preview.get("tree"):
            reset_main_to_head(root)
            state["preview"] = None
            print("已重置上一轮 switch 预览，主项目目录已恢复到当前提交。")
            return True
        raise WorktreeError(
            "主项目目录存在未提交改动，且不等于已记录的 switch 预览状态，已停止。\n"
            "请先手动提交、stash 或清理这些改动后再继续。\n\n"
            f"{status}"
        )

    if preview:
        state["preview"] = None
        reset_main_to_head(root)
        print("已清除 switch 预览记录，主项目目录已恢复到当前提交。")
        return True

    reset_main_to_head(root)
    if required:
        print("当前没有已记录的 switch 预览状态，主项目目录已恢复到当前提交。")
    return False


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

    main_commit = text(["git", "rev-parse", "HEAD"], root)
    task_head = text(["git", "rev-parse", "HEAD"], task_path)
    main_tree = head_tree(root)
    task_tree = tree_from_worktree(task_path)

    if task_head == main_commit:
        task["status"] = "active"
        task["last_synced_at"] = now()
        task["updated_at"] = now()
        return "已包含主项目最新提交"

    if task_tree == main_tree:
        reset_task_to_commit(task_path, main_commit)
        task["status"] = "active"
        task["last_synced_at"] = now()
        task["updated_at"] = now()
        return "任务内容已与主项目一致，已自动对齐到主项目最新提交"

    changes = task_changes(task_path)
    if changes and task_changes_absorbed_by_main(root, task_path, changes):
        reset_task_to_commit(task_path, main_commit)
        task["status"] = "active"
        task["last_synced_at"] = now()
        task["updated_at"] = now()
        return "任务本地改动已被主项目吸收，已自动对齐到主项目最新提交"

    result = run(["git", "merge", "--ff-only", main_commit], task_path, check=False)
    if result.returncode != 0:
        stdout = result.stdout.decode(errors="replace").strip()
        stderr = result.stderr.decode(errors="replace").strip()
        raise WorktreeError(
            "任务目录无法直接拉取主项目最新提交，已停止。\n"
            "请先在任务目录手动处理主线更新、提交关系或冲突后再继续。\n\n"
            f"stdout:\n{stdout}\n"
            f"stderr:\n{stderr}"
        )

    task["status"] = "active"
    task["last_synced_at"] = now()
    task["updated_at"] = now()
    return "已带入主项目最新提交"


def sync_conflict_advice(name):
    return (
        f"任务同步遇到冲突，已停止: {name}\n"
        "建议处理方式:\n"
        "1. 先在任务 worktree 中手动提交、stash 或处理会被主线覆盖的改动，再重新同步。\n"
        "2. 让 Codex 在任务 worktree 中手动把主项目最新提交合入任务分支。\n"
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

    slug = branch_slug(name)
    repo_name = root.name
    base_dir = root.parent / f"{repo_name}.worktrees"
    worktree = (base_dir / worktree_dir_name(name)).resolve()
    branch = f"worktree/{slug}"
    if worktree.exists():
        raise WorktreeError(f"任务目录已存在: {worktree}")
    existing_branches = text(["git", "branch", "--list", branch], root)
    if existing_branches:
        raise WorktreeError(f"任务分支已存在: {branch}")

    base_dir.mkdir(parents=True, exist_ok=True)
    run(["git", "worktree", "add", "-b", branch, str(worktree), "HEAD"], root)
    state["tasks"][name] = {
        "name": name,
        "slug": slug,
        "branch": branch,
        "worktree": str(worktree),
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
    if state.get("preview") and not main_status(root):
        state["preview"] = None
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
            changes = task_changes(path)
            if changes:
                dirty = "已被主线吸收" if task_changes_absorbed_by_main(root, path, changes) else "有未合并改动"
            else:
                dirty = "干净"
        print(f"- {name}")
        print(f"  状态: {task.get('status', 'unknown')} / {dirty} / 目录{exists}")
        print(f"  分支: {task['branch']}")
        print(f"  目录: {task['worktree']}")
        print(f"  更新时间: {task.get('updated_at')}")


def cmd_merge(args):
    root = require_main_project_dir()
    state = load_state(root)
    task = get_task(state, args.name.strip())
    task_path = Path(task["worktree"])
    if not task_path.exists():
        raise WorktreeError(f"任务目录不存在: {task_path}")

    changes = task_changes(task_path)
    if not changes:
        state["preview"] = None
        save_state(root, state)
        print(f"任务没有待合并改动: {task['name']}")
        return
    task_tree = tree_from_worktree(task_path)
    patch = task_worktree_patch(task_path, task_tree)
    if not patch:
        state["preview"] = None
        save_state(root, state)
        print(f"任务没有待合并改动: {task['name']}")
        return

    reset_main_slot(root, state)
    state["preview"] = None
    save_state(root, state)
    main_commit = text(["git", "rev-parse", "HEAD"], root)

    print("待合并文件:")
    print(format_changes(changes))
    apply_task_patch(root, patch)

    reset_task_to_commit(task_path, main_commit)

    task["status"] = "merged-to-main-pending-user-commit"
    task["last_merged_at"] = now()
    task["last_synced_at"] = now()
    task["updated_at"] = now()
    save_state(root, state)

    print("已把任务改动三方合并到主项目目录，主项目未自动 commit。")
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
                if "无法直接拉取主项目最新提交" in message:
                    print(sync_conflict_advice(name))
        return

    name = (args.name or "").strip()
    validate_task_name(name)
    try:
        result = sync_one_task(root, state, name)
    except WorktreeError as exc:
        message = str(exc)
        if "无法直接拉取主项目最新提交" in message:
            raise WorktreeError(f"{message}\n\n{sync_conflict_advice(name)}")
        raise
    save_state(root, state)
    print(result)


def sh_quote(value):
    return "'" + value.replace("'", "'\"'\"'") + "'"


def validate_sql_path(path):
    rel_path = validate_relative_path(path)
    if Path(rel_path).suffix.lower() != ".sql":
        raise WorktreeError(f"SQL 命令只支持 .sql 文件: {path}")
    return rel_path


def collect_sql_paths(paths):
    sql_paths = []
    seen = set()
    for path in paths:
        rel_path = validate_sql_path(path)
        if rel_path in seen:
            raise WorktreeError(f"重复指定 SQL 文件: {rel_path}")
        seen.add(rel_path)
        sql_paths.append(rel_path)
    return sql_paths


def prepare_sql_take(root, state, name, sql_paths, command_name):
    task = get_task(state, name)
    task_path = Path(task["worktree"])
    if not task_path.exists():
        raise WorktreeError(f"任务目录不存在: {task_path}")

    changes_by_path = change_map(task_changes(task_path))
    for rel_path in sql_paths:
        status = changes_by_path.get(rel_path)
        if status != "A":
            raise WorktreeError(
                f"${command_name} 只支持从任务目录拿取新增且未合并的 SQL 文件。\n"
                f"文件: {rel_path}\n"
                f"当前状态: {status or '未变化'}"
            )
        src = task_path / rel_path
        if src.is_symlink():
            raise WorktreeError(f"不支持拿取符号链接 SQL 文件: {rel_path}")
        if not src.is_file():
            raise WorktreeError(f"任务 SQL 文件不存在或不是普通文件: {rel_path}")
    return task, task_path


def take_sql_files(root, state, task_path, sql_paths):
    reset_main_slot(root, state)
    save_state(root, state)

    for rel_path in sql_paths:
        dst = root / rel_path
        if dst.exists() or dst.is_symlink():
            raise WorktreeError(f"主项目目录已存在同路径文件，已停止: {rel_path}")

    taken = []
    try:
        for rel_path in sql_paths:
            src = task_path / rel_path
            dst = root / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            src.unlink()
            run(["git", "rm", "--cached", "--ignore-unmatch", "--", rel_path], task_path)
            taken.append(rel_path)
    except OSError as exc:
        raise WorktreeError(f"拿取 SQL 文件失败: {exc}") from exc
    return taken


def cmd_take_sql(args):
    root = require_main_project_dir()
    state = load_state(root)

    name = args.name.strip()
    validate_task_name(name)
    sql_paths = collect_sql_paths(args.sql_paths)
    task, task_path = prepare_sql_take(root, state, name, sql_paths, "worktree-take-sql")

    taken = take_sql_files(root, state, task_path, sql_paths)

    task["status"] = "active"
    task["last_sql_taken_at"] = now()
    task["updated_at"] = now()
    state["preview"] = None
    save_state(root, state)

    print(f"已从任务拿取 SQL: {task['name']}")
    for rel_path in taken:
        print(f"- {rel_path}")
    print("这些 SQL 已复制到主项目目录，并已从任务 worktree 删除。")
    print("请在主项目目录 review 后手动提交，然后执行:")
    print(f"$worktree-sync {task['name']}")


def commit_sql(root, sql_paths):
    run(["git", "add", "--", *sql_paths], root)
    message = "add " + " ".join(sql_paths)
    run(["git", "commit", "-m", message], root)
    return message


def push_current_branch(root):
    run(["git", "push"], root)


def same_file_content(left, right):
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as left_file, right.open("rb") as right_file:
        while True:
            left_chunk = left_file.read(1024 * 1024)
            right_chunk = right_file.read(1024 * 1024)
            if left_chunk != right_chunk:
                return False
            if not left_chunk:
                return True


def sync_sql_files_to_task(root, task, sql_paths):
    task_path = Path(task["worktree"])
    if not task_path.exists():
        raise WorktreeError(f"任务目录不存在: {task_path}")

    copied = []
    already_present = []
    for rel_path in sql_paths:
        src = root / rel_path
        dst = task_path / rel_path
        if not src.is_file() or src.is_symlink():
            raise WorktreeError(f"主项目 SQL 文件不存在或不是普通文件: {rel_path}")
        if dst.exists() or dst.is_symlink():
            if dst.is_file() and not dst.is_symlink() and same_file_content(src, dst):
                already_present.append(rel_path)
                continue
            raise WorktreeError(
                "任务目录已有同路径 SQL，且内容与主线 SQL 不一致，已停止同步。\n"
                f"文件: {rel_path}"
            )
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(rel_path)

    task["status"] = "active"
    task["last_sql_synced_at"] = now()
    task["updated_at"] = now()
    if copied and already_present:
        return f"已同步 SQL {len(copied)} 个，已存在 {len(already_present)} 个"
    if copied:
        return f"已同步 SQL {len(copied)} 个"
    return "SQL 已存在"


def sync_sql_files_to_tasks(root, state, sql_paths):
    synced = []
    failed = []
    for name in list(state["tasks"].keys()):
        try:
            task = get_task(state, name)
            result = sync_sql_files_to_task(root, task, sql_paths)
            save_state(root, state)
            synced.append((name, result))
        except WorktreeError as exc:
            failed.append((name, str(exc)))
    return synced, failed


def switch_to_task(root, state, name):
    task = get_task(state, name)
    task_path = Path(task["worktree"])
    if not task_path.exists():
        raise WorktreeError(f"任务目录不存在: {task_path}")

    changes = task_changes(task_path)
    reset_main_slot(root, state)
    if not changes:
        state["preview"] = None
        save_state(root, state)
        print(f"任务没有可预览改动: {task['name']}")
        return

    print("待预览文件:")
    print(format_changes(changes))
    apply_task_files(task_path, root, changes)
    preview_tree = tree_from_worktree(root)
    state["preview"] = {
        "task": task["name"],
        "slug": task["slug"],
        "head": text(["git", "rev-parse", "HEAD"], root),
        "tree": preview_tree,
        "files": [path for _status, path in changes],
        "switched_at": now(),
    }
    save_state(root, state)

    print(f"已切换主项目目录到任务预览状态: {task['name']}")
    print("该操作只用于临时验证；不会更新任务基线、不会反向同步、不会自动 commit。")


def cmd_push_sql(args):
    root = require_main_project_dir()
    state = load_state(root)

    name = args.name.strip()
    validate_task_name(name)
    sql_paths = collect_sql_paths(args.sql_paths)
    task, task_path = prepare_sql_take(root, state, name, sql_paths, "worktree-push-sql")

    taken = take_sql_files(root, state, task_path, sql_paths)
    task["status"] = "active"
    task["last_sql_taken_at"] = now()
    task["updated_at"] = now()
    state["preview"] = None
    save_state(root, state)

    print(f"已从任务拿取 SQL: {task['name']}")
    for rel_path in taken:
        print(f"- {rel_path}")

    message = commit_sql(root, taken)
    print(f"已提交 SQL: {message}")

    push_current_branch(root)
    print("已执行 git push。")

    synced, failed = sync_sql_files_to_tasks(root, state, taken)
    if synced:
        print("已向任务同步 SQL:")
        for task_name, result in synced:
            print(f"- {task_name}: {result}")
    if failed:
        print("以下任务 SQL 同步被阻止:")
        for task_name, message_text in failed:
            print(f"- {task_name}")
            print(message_text)
        if any(task_name == name for task_name, _message in failed):
            raise WorktreeError("当前 SQL 对应任务同步失败，已停止切换预览。")

    switch_to_task(root, state, name)


def cmd_switch(args):
    root = require_main_project_dir()
    state = load_state(root)

    if args.clear:
        if args.name:
            raise WorktreeError("$worktree-switch --clear 不能同时指定任务名。")
        reset_main_slot(root, state, required=True)
        save_state(root, state)
        return

    name = (args.name or "").strip()
    validate_task_name(name)
    switch_to_task(root, state, name)


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
        changes = task_changes(task_path)
        if changes and not args.force:
            if task_changes_absorbed_by_main(root, task_path, changes):
                print("任务 worktree 还有本地改动，但这些改动已包含在主项目当前提交中，继续清理。")
            else:
                print("任务 worktree 还有未合并改动，已停止清理。")
                print("未合并文件:")
                print(format_changes(changes))
                print("请先执行 $worktree-merge，或确认放弃后让 Codex 使用 --force。")
                return
        run(["git", "worktree", "remove", "--force", str(task_path)], root)

    branch_exists = text(["git", "branch", "--list", task["branch"]], root)
    if branch_exists:
        run(["git", "branch", "-D", task["branch"]], root)

    del state["tasks"][name]
    save_state(root, state)
    print(f"已清理 worktree 任务: {name}")


def cmd_status(_args):
    root, current_root, task_name, _task = repo_context()
    print(f"当前 Git 仓库: {current_root}")
    if task_name:
        print(f"当前 worktree 任务: {task_name}")
        print(f"主项目目录: {root}")
    else:
        print("当前位于主项目目录。")

    output = run(
        ["git", "status", "--short", "--branch", "--untracked-files=all"],
        current_root,
    ).stdout.decode(errors="replace").rstrip("\n")
    if output:
        print(output)
    else:
        print("工作区干净。")


def cmd_help(_args):
    print(
        """codex-cli-worktree helper

Internal subcommands:
  new <name>
  list
  info <name>
  current
  status
  switch <name>
  switch --clear
  merge <name>
  sync <name>
  sync --all
  take-sql <name> <sql> [sql...]
  push-sql <name> <sql> [sql...]
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

    p = sub.add_parser("take-sql")
    p.add_argument("name")
    p.add_argument("sql_paths", nargs="+")
    p.set_defaults(func=cmd_take_sql)

    p = sub.add_parser("push-sql")
    p.add_argument("name")
    p.add_argument("sql_paths", nargs="+")
    p.set_defaults(func=cmd_push_sql)

    p = sub.add_parser("switch")
    p.add_argument("name", nargs="?")
    p.add_argument("--clear", action="store_true")
    p.set_defaults(func=cmd_switch)

    p = sub.add_parser("current")
    p.set_defaults(func=cmd_current)

    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)

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
