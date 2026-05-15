---
name: worktree-help
description: 说明 codex-cli-worktree 并行 Git worktree Skills 的用法。用户输入 $worktree-help 时使用。
---

# worktree-help

当用户输入 `$worktree-help` 或要求查看 worktree 命令帮助时使用本 skill。

## 执行要求

- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" help`。
- 用简体中文补充说明推荐流程：
  1. 在主项目目录执行 `$worktree-new 任务名`。
  2. 在任务目录开发，不启动项目服务。
  3. 回主项目目录执行 `$worktree-merge 任务名`。
  4. 用户手动重启服务验证。
  5. 验证通过后用户手动 commit。
  6. 执行 `$worktree-end 任务名` 清理任务。
  7. 如需查找任务目录，执行 `$worktree-info 任务名`。
