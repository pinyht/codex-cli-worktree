---
name: worktree-switch
description: 将指定 codex-cli-worktree 任务的当前代码临时切换到主项目目录用于验证，或清除当前预览状态。用户输入 $worktree-switch 任务名 或 $worktree-switch --clear 时使用。
---

# worktree-switch

当用户输入 `$worktree-switch 任务名`、`$worktree-switch --clear`，或要求临时切换/预览 worktree 任务效果时使用本 skill。

## 执行要求

- 必须在主项目目录执行。
- 如果用户输入 `$worktree-switch --clear`，调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" switch --clear`。
- 否则从用户输入中提取任务名；任务名不能为空，且不能以 `-` 开头。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" switch "任务名"`。
- 不要启动任何项目服务。
- switch 只用于主项目目录临时验证，不更新任务同步基线，不反向同步任务 worktree，不自动 commit。
- 如果脚本提示主项目目录存在非 switch 产生的未提交改动，停止并提示用户先提交、清理或手动处理。
- 如果脚本提示补丁无法自动应用，停止自动处理；读取脚本输出的补丁路径、冲突文件和相关代码，给出 1-3 个解决方案让用户选择。
