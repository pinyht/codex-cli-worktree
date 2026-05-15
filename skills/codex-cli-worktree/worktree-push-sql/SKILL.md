---
name: worktree-push-sql
description: 将任务 worktree 中新增的 SQL 文件提交并推送到主项目，然后同步所有任务并切换到该任务预览。用户输入 $worktree-push-sql 任务名 SQL文件... 时使用。
---

# worktree-push-sql

当用户输入 `$worktree-push-sql 任务名 SQL文件...`，或要求一键把任务 worktree 的 SQL 迁移文件提交到主线并切回该任务预览时使用本 skill。

## 执行要求

- 必须在主项目目录执行。
- 从用户输入中提取任务名和一个或多个 SQL 文件路径；任务名不能为空。
- 只接受 `.sql` 文件路径；多个 SQL 文件用空格分开。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" push-sql "任务名" "SQL文件1" "SQL文件2"`。
- 不要启动任何项目服务。
- 该命令会自动执行高副作用流程：拿取 SQL、删除任务 worktree 内对应 SQL、`git add`、`git commit`、`git push`、同步全部任务、切换到指定任务预览。
- 提交信息由脚本自动生成，格式为 `add SQL文件 SQL文件`。
- 如果 push 或当前任务同步失败，停止并按脚本输出处理。
- 成功后提醒用户：主项目目录已切换到该任务预览，可手动启动服务或运行项目验证命令。
