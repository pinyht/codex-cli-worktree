---
name: worktree-resume
description: 输出指定 codex-cli-worktree 任务目录和状态，方便继续任务。用户输入 $worktree-resume 任务名时使用。
---

# worktree-resume

当用户输入 `$worktree-resume 任务名` 或要求继续指定 worktree 任务时使用本 skill。

## 执行要求

- 建议在主项目目录执行。
- 从用户输入中提取任务名；任务名不能为空。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" resume "任务名"`。
- 不要启动任何项目服务。
- 成功后，后续所有开发、测试、文件读取和修改都应以脚本输出的任务目录作为工作目录。
