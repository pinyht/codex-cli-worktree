---
name: worktree-current
description: 查看当前 Codex CLI 窗口对应的 worktree 任务，或查看主项目目录当前是否处于 switch 预览/主线基线状态。用户输入 $worktree-current 时使用。
---

# worktree-current

当用户输入 `$worktree-current`，或要求查看当前窗口属于哪个 worktree 任务时使用本 skill。

## 执行要求

- 可以在主项目目录或任务 worktree 目录执行。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" current`。
- 不要启动任何项目服务。
- 如果当前在任务 worktree，向用户说明任务名、主项目目录和任务目录。
- 如果当前在主项目目录，向用户说明当前是 switch 预览状态、主线基线状态，还是存在未提交改动。
