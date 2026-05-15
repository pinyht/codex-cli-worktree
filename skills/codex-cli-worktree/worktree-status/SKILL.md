---
name: worktree-status
description: 查看当前 Codex CLI 窗口所在 Git 仓库的未提交文件状态。用户输入 $worktree-status 时使用。
---

# worktree-status

当用户输入 `$worktree-status`，或要求查看当前窗口有哪些未提交文件时使用本 skill。

## 执行要求

- 可在主项目目录或任务 worktree 执行。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" status`。
- 不要启动任何项目服务。
- 不要修改文件。
- 该命令输出当前 Git 仓库路径、任务名信息，以及 `git status --short --branch --untracked-files=all` 的结果，方便查看新增 SQL 文件名和路径。
