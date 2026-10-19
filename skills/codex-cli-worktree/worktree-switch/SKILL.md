---
name: worktree-switch
description: 将指定 codex-cli-worktree 任务的当前代码临时切换到主项目目录用于验证，或清除当前预览状态。仅在用户输入 $worktree-switch 任务名 或 $worktree-switch --clear 时执行。
---

# worktree-switch

当用户输入 `$worktree-switch 任务名`、`$worktree-switch --clear` 时使用本 skill。

## 执行要求

- 必须在主项目目录执行。
- 如果用户输入 `$worktree-switch --clear`，调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" switch --clear`。
- 否则从用户输入中提取任务名；任务名不能为空，不能包含空白字符，且不能以 `-` 开头或结尾。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" switch "任务名"`。
- 如果命令因为沙箱或文件系统权限失败，例如出现 `.git/index.lock: Read-only file system`、`Permission denied`、无法写入 Git 索引或无法写入主项目目录，必须用同一个命令重新执行并申请 `require_escalated` 提权。
- 不要启动任何项目服务。
- switch 只用于主项目目录临时验证，不更新任务同步基线，不反向同步任务 worktree，不自动 commit。
- switch 会在主项目目录干净或等于已记录的 switch 预览时，自动把主项目目录恢复到当前提交并清理新增文件，再复制任务目录里的改动。
- 如果脚本提示主项目目录存在非 switch 产生的未提交改动，停止并提示用户先提交、stash、清理或手动处理。
- 如果脚本提示任务分支上有主线没有的提交，停止并向用户说明：这些提交不会出现在预览里；让用户按脚本输出的 `git reset --soft <提交>` 在任务目录把改动退回工作区后重试，不要绕过这个检查。
- 脚本以非零退出码表示操作被阻止或未完成；遇到非零退出码时先说明原因，不要自动重试，也不要用其他方式绕过约束。
