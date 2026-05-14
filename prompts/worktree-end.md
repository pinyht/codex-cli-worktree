你正在执行项目自定义命令 `/worktree-end`。

目标：清理指定 worktree 任务，包括任务目录、任务分支和本地状态记录。

参数：
- 任务名来自命令后的文本，即 `$ARGUMENTS`。
- 如果 `$ARGUMENTS` 未被替换，请从用户原始输入中提取任务名。

执行要求：
- 必须在主项目目录执行。
- 调用 `python3 "$HOME/.codex/scripts/worktree-task.py" end "$ARGUMENTS"`。
- 不要启动任何项目服务。
- 如果脚本提示还有未合并改动，停止并询问用户是先合并还是明确放弃。
- 不要擅自使用 `--force`。
