---
name: worktree-new
description: 创建新的 codex-cli-worktree 并行 Git worktree 任务。用户输入 $worktree-new 任务名时使用。
---

# worktree-new

当用户输入 `$worktree-new 任务名` 或要求创建新的 worktree 并行任务时使用本 skill。

## 执行要求

- 必须在主项目目录执行。
- 从用户输入中提取任务名；任务名不能为空，不能包含空格、Tab、换行、路径分隔符或路径非法字符，且不能以 `-` 开头或结尾。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" new "任务名"`。
- 不要启动任何项目服务。
- 如果脚本提示主项目目录不干净、任务已存在、分支已存在或目录已存在，停止并把原因告诉用户。
- 成功后告诉用户任务目录，并提示用户在该目录打开新的 Codex CLI 继续开发。
