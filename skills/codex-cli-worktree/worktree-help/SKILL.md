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
$worktree-merge <任务名>    合并任务改动到主项目，不自动 commit，并反向同步
$worktree-sync <任务名>     把主项目当前文件同步到任务 worktree
$worktree-end <任务名>      清理任务 worktree、任务分支和任务状态
$worktree-help              查看本帮助
```

推荐流程：

1. 在主项目目录执行 `$worktree-new 任务名`。
2. 按输出的 `cd ... && codex` 命令，在任务目录打开新的 Codex CLI。
3. 在任务目录开发，不启动长期运行的项目服务。
4. 回主项目目录执行 `$worktree-merge 任务名`。
5. 用户手动重启服务或运行验证命令。
6. 验证通过后用户手动 commit。
7. 执行 `$worktree-end 任务名` 清理任务。
8. 如需查找任务目录，执行 `$worktree-info 任务名`。

说明：

- 主项目目录用于创建、合并、验证和手动 commit。
- 任务目录用于具体开发。
- `$worktree-info` 只查询任务信息，不会自动切换当前 Codex CLI 会话目录。
