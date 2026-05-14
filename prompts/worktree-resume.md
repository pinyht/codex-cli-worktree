你正在执行项目自定义命令 `/worktree-resume`。

目标：在新会话或当前会话中继续指定 worktree 任务。

参数：
- 任务名来自命令后的文本，即 `$ARGUMENTS`。
- 如果 `$ARGUMENTS` 未被替换，请从用户原始输入中提取任务名。

执行要求：
- 建议在主项目目录执行。
- 调用 `python3 "$HOME/.codex/scripts/worktree-task.py" resume "$ARGUMENTS"`。
- 不要启动任何项目服务。
- 成功后，后续所有开发、测试、文件读取和修改都应以脚本输出的任务目录作为工作目录。
- 如果任务涉及 `app/`、`admin/`、`license/`，继续遵守对应 AGENTS.md 和 docs 规则。
