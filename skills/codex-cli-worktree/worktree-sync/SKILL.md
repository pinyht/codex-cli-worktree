---
name: worktree-sync
description: 将主项目最新提交带到指定或所有 codex-cli-worktree 任务目录。用户输入 $worktree-sync 任务名 或 $worktree-sync --all 时使用。
---

# worktree-sync

当用户输入 `$worktree-sync 任务名`、`$worktree-sync --all` 或要求同步 worktree 任务时使用本 skill。

## 执行要求

- 必须在主项目目录执行。
- 如果用户输入 `$worktree-sync --all`，调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" sync --all`。
- 否则从用户输入中提取任务名；任务名不能为空，不能包含空白字符，且不能以 `-` 开头或结尾。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" sync "任务名"`。
- 不要启动任何项目服务。
- sync 执行前主项目目录必须没有未提交改动。
- sync 的效果类似在任务目录拉取主线：把主项目最新提交带到任务目录；如果任务本地改动已经被主项目吸收，脚本会自动把任务目录重置对齐到主线。
- 如果脚本提示任务目录无法直接拉取主项目最新提交，停止自动处理；根据脚本输出说明需要先在任务目录处理冲突、提交关系或会被覆盖的改动。
- 不提供也不要使用 `--force`。
