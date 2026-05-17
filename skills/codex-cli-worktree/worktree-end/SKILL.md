---
name: worktree-end
description: 清理指定 codex-cli-worktree 任务的 worktree、分支和本地状态。用户输入 $worktree-end 任务名时使用。
---

# worktree-end

当用户输入 `$worktree-end 任务名` 或要求清理 worktree 任务时使用本 skill。

## 执行要求

- 必须在主项目目录执行。
- 从用户输入中提取任务名；任务名不能为空。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" end "任务名"`。
- 不要启动任何项目服务。
- 如果脚本提示任务改动已包含在主项目当前提交中，可以继续清理，这是正常结果。
- 如果脚本提示还有未合并改动，停止并询问用户是先合并还是明确放弃。
- 不要擅自使用 `--force`。
