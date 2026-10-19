---
name: worktree-new
description: 创建新的 codex-cli-worktree 并行 Git worktree 任务。仅在用户输入 $worktree-new 任务名时执行。
---

# worktree-new

当用户输入 `$worktree-new 任务名` 时使用本 skill。

## 执行要求

- 必须在主项目目录执行。
- 从用户输入中提取任务名；任务名不能为空，不能包含空格、Tab、换行、路径分隔符或路径非法字符，且不能以 `-` 开头或结尾。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" new "任务名"`。
- 不要启动任何项目服务。
- 如果脚本提示主项目目录不干净、任务已存在、分支已存在或目录已存在，停止并把原因告诉用户。
- 成功后必须把脚本输出的 `继续开发命令（复制以下整行）:` 下一行原样放在最终回复的代码块中，例如：

  ```bash
  cd '/path/to/repo.codex-worktrees/task-任务名-xxxxxxxx' && codex
  ```

  不要只给任务目录，不要省略 `&& codex`，不要改写路径。
- 再提醒用户在该目录打开新的 Codex CLI 继续开发；不要启动项目服务。
