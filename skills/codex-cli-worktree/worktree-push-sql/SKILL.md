---
name: worktree-push-sql
description: 将任务 worktree 中新增的 SQL 文件提交并推送到主项目，然后把本次 SQL 同步到各任务并切换到该任务预览。仅在用户输入 $worktree-push-sql 任务名 SQL文件... 时执行。
---

# worktree-push-sql

当用户输入 `$worktree-push-sql 任务名 SQL文件...` 时使用本 skill。

## 执行要求

- 必须在主项目目录执行。
- 从用户输入中提取任务名和一个或多个 SQL 文件路径；任务名不能为空。
- 只接受 `.sql` 文件路径；多个 SQL 文件用空格分开。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" push-sql "任务名" "SQL文件1" "SQL文件2"`。
- 不要启动任何项目服务。
- 该命令会自动执行高副作用流程：拿取 SQL、删除任务 worktree 内对应 SQL、`git add`、`git commit`、`git push`、把本次 SQL 文件同步到各任务、切换到指定任务预览。
- 提交信息由脚本自动生成，格式为 `add SQL文件 SQL文件`。
- 如果 push 或当前任务 SQL 同步失败，停止并按脚本输出处理。
- 部分任务 SQL 同步失败时，脚本会以非零退出码结束；先说明哪些任务失败以及原因，不要自动重试或绕过。
- SQL 同步只同步本次 SQL 文件，不执行完整 `$worktree-sync --all`。
- 成功后提醒用户：主项目目录已切换到该任务预览，可手动启动服务或运行项目验证命令。
- 脚本以非零退出码表示操作被阻止或未完成；遇到非零退出码时先说明原因，不要自动重试，也不要用其他方式绕过约束。
