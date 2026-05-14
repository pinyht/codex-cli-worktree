你正在执行项目自定义命令 `/worktree-sync`。

目标：把主项目目录当前文件同步回指定 worktree 任务目录，让任务继续基于最新主项目代码开发。

参数：
- 任务名来自命令后的文本，即 `$ARGUMENTS`。
- 如果 `$ARGUMENTS` 未被替换，请从用户原始输入中提取任务名。

执行要求：
- 建议在主项目目录执行。
- 调用 `python3 "$HOME/.codex/scripts/worktree-task.py" sync "$ARGUMENTS"`。
- 不要启动任何项目服务。
- 如果脚本提示任务 worktree 有未合并改动，停止并说明应先 `/worktree-merge`，除非用户明确确认放弃这些改动。
- 不要擅自使用 `--force`。
