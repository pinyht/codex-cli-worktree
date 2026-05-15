---
name: worktree-info
description: 查看指定 codex-cli-worktree 任务的状态、分支和任务目录。用户输入 $worktree-info 任务名时使用。
---

# worktree-info

当用户输入 `$worktree-info 任务名`，或要求查看指定 worktree 任务信息、查找任务目录时使用本 skill。

## 执行要求

- 建议在主项目目录执行。
- 从用户输入中提取任务名；任务名不能为空。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" info "任务名"`。
- 不要启动任何项目服务。
- 成功后，向用户说明这是任务信息查询，不会自动切换当前 Codex CLI 会话目录。
- 如果用户要继续开发，提示使用脚本输出的 `cd ... && codex` 命令在任务目录打开新的 Codex CLI。
