---
name: worktree-sync
description: 将主项目当前文件同步到指定 codex-cli-worktree 任务目录。用户输入 $worktree-sync 任务名时使用。
---

# worktree-sync

当用户输入 `$worktree-sync 任务名` 或要求同步 worktree 任务时使用本 skill。

## 执行要求

- 建议在主项目目录执行。
- 从用户输入中提取任务名；任务名不能为空。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" sync "任务名"`。
- 不要启动任何项目服务。
- 如果脚本提示任务 worktree 有未合并改动，停止并说明应先 `$worktree-merge`，除非用户明确确认放弃这些改动。
- 不要擅自使用 `--force`。
