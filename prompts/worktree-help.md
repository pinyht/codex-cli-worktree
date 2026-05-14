你正在执行项目自定义命令 `/worktree-help`。

目标：说明 worktree 并行开发命令的用法。

执行要求：
- 调用 `python3 "$HOME/.codex/scripts/worktree-task.py" help`。
- 用简体中文补充说明推荐流程：
  1. 在主项目目录 `/worktree-new 任务名`。
  2. 在任务目录开发，不启动项目服务。
  3. 回主项目目录 `/worktree-merge 任务名`。
  4. 用户手动重启服务验证。
  5. 验证通过后用户手动 commit。
  6. `/worktree-end 任务名` 清理任务。
