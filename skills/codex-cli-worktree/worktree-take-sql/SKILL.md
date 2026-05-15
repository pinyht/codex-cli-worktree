---
name: worktree-take-sql
description: 将任务 worktree 中新增的 SQL 文件拿到主项目目录并从任务目录删除。用户输入 $worktree-take-sql 任务名 SQL文件... 时使用。
---

# worktree-take-sql

当用户输入 `$worktree-take-sql 任务名 SQL文件...`，或要求把任务 worktree 的 SQL 迁移文件提前拿到主项目目录时使用本 skill。

## 执行要求

- 必须在主项目目录执行。
- 从用户输入中提取任务名和一个或多个 SQL 文件路径；任务名不能为空。
- 只接受 `.sql` 文件路径；多个 SQL 文件用空格分开。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" take-sql "任务名" "SQL文件1" "SQL文件2"`。
- 不要启动任何项目服务。
- 不要自动 commit。
- 命令会把任务 worktree 中新增且未合并的 SQL 文件复制到主项目目录，并删除任务 worktree 内对应文件。
- 成功后提醒用户：先在主项目目录 review 并手动 commit SQL，再执行 `$worktree-sync 任务名` 把该提交同步回任务 worktree。
