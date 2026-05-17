---
name: worktree-help
description: 说明 codex-cli-worktree 并行 Git worktree Skills 的用法。用户输入 $worktree-help 时使用。
---

# worktree-help

当用户输入 `$worktree-help` 或要求查看 worktree 命令帮助时使用本 skill。

## 执行要求

- 不要调用脚本。
- 不要运行任何命令。
- 直接用简体中文输出下面的帮助内容。

## 帮助内容

worktree 并行开发命令：

```text
$worktree-new <任务名>      创建任务 worktree 和任务分支
$worktree-list              查看当前仓库的任务列表
$worktree-info <任务名>     查看任务状态、分支、任务目录和继续开发命令
$worktree-current           查看当前窗口对应任务，或主目录当前状态
$worktree-status            查看当前窗口 Git 未提交状态
$worktree-switch <任务名>   恢复主项目目录后临时复制任务改动用于验证
$worktree-switch --clear    清除 switch 预览，恢复主项目目录并清理新增文件
$worktree-merge <任务名>    恢复主项目目录后复制任务改动到主项目，不自动 commit
$worktree-sync <任务名>     把主项目最新提交带到任务目录
$worktree-sync --all        把主项目最新提交带到所有任务目录
$worktree-take-sql <任务名> <sql...>
                            把任务新增 SQL 拿到主目录并从任务目录删除
$worktree-push-sql <任务名> <sql...>
                            拿取任务新增 SQL，自动 commit/push，同步本次 SQL 并切到任务预览
$worktree-end <任务名>      清理任务 worktree、任务分支和任务状态
$worktree-help              查看本帮助
```

推荐流程：

1. 在主项目目录执行 `$worktree-new 任务名`。
2. 按输出的 `cd ... && codex` 命令，在任务目录打开新的 Codex CLI。
3. 在任务目录开发，不启动长期运行的项目服务。
4. 需要临时看效果时，回主项目目录执行 `$worktree-switch 任务名`。
5. 确认任务完成后，回主项目目录执行 `$worktree-merge 任务名`。
6. 用户手动重启服务或运行验证命令。
7. 验证通过后用户手动 commit。
8. 主项目有新提交后，可执行 `$worktree-sync --all` 带到未完成任务。
9. 执行 `$worktree-end 任务名` 清理任务。
10. 如需查看当前窗口任务名，执行 `$worktree-current`。
11. 如需查看当前窗口未提交文件，执行 `$worktree-status`。
12. 如果任务产生数据库迁移 SQL，可先在主项目目录执行 `$worktree-take-sql 任务名 migrations/1.sql`，手动 commit 后再 `$worktree-sync 任务名`。
13. 如果希望一键提交并切回任务预览，可执行 `$worktree-push-sql 任务名 migrations/1.sql`。

说明：

- 主项目目录是可重置的统一调试槽，用于创建、合并、验证和手动 commit。
- 任务目录用于具体开发。
- 任务名必须是单个参数，不能包含空格、Tab、换行、路径分隔符或路径非法字符，且不能以 `-` 开头或结尾；新任务目录名会包含完整任务名。
- `$worktree-switch` 只用于临时预览，不更新任务基线、不自动 commit；主目录有非 switch 产生的未提交改动时会停止。
- `$worktree-info` 只查询任务信息，不会自动切换当前 Codex CLI 会话目录。
