你正在执行项目自定义命令 `/worktree-new`。

目标：为用户提供的任务名创建一个独立 Git worktree 任务目录和任务分支，用于并行开发。

参数：
- 任务名来自命令后的文本，即 `$ARGUMENTS`。
- 如果 `$ARGUMENTS` 未被替换，请从用户原始输入中提取任务名。

执行要求：
- 必须在主项目目录执行。
- 调用 `python3 "$HOME/.codex/scripts/worktree-task.py" new "$ARGUMENTS"`。
- 不要启动任何项目服务。
- 如果脚本提示主项目目录不干净、任务已存在、分支已存在或目录已存在，停止并把原因告诉用户。
- 成功后告诉用户任务目录，并提示用户在该目录打开新的 Codex CLI 继续开发。
- 如果后续开发涉及 `app/`、`admin/`、`license/`，仍必须遵守对应 AGENTS.md 和 docs 规则。
