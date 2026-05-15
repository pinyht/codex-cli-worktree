---
name: worktree-sync
description: 将主项目当前文件同步到指定或所有 codex-cli-worktree 任务目录。用户输入 $worktree-sync 任务名 或 $worktree-sync --all 时使用。
---

# worktree-sync

当用户输入 `$worktree-sync 任务名`、`$worktree-sync --all` 或要求同步 worktree 任务时使用本 skill。

## 执行要求

- 必须在主项目目录执行。
- 如果用户输入 `$worktree-sync --all`，调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" sync --all`。
- 否则从用户输入中提取任务名；任务名不能为空，且不能以 `-` 开头。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" sync "任务名"`。
- 不要启动任何项目服务。
- sync 执行前主项目目录必须没有未提交改动。
- 如果脚本提示任务同步冲突，停止自动处理；读取脚本输出的补丁路径、冲突文件和相关代码，给出 1-3 个解决方案让用户选择。
- 不提供也不要使用 `--force`。
