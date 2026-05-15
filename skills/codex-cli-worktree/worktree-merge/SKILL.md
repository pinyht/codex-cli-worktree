---
name: worktree-merge
description: 将 codex-cli-worktree 任务改动合并回主项目目录但不自动 commit。用户输入 $worktree-merge 任务名时使用。
---

# worktree-merge

当用户输入 `$worktree-merge 任务名` 或要求合并 worktree 任务时使用本 skill。

## 执行要求

- 必须在主项目目录执行。
- 从用户输入中提取任务名；任务名不能为空。
- 调用 `python3 "$HOME/.agents/skills/codex-cli-worktree/scripts/worktree-task.py" merge "任务名"`。
- 不要启动任何项目服务。
- 合并成功后，脚本会把主项目合并后的文件反向同步到任务 worktree，并更新任务同步基线。
- 合并成功后提醒用户：在主项目目录手动重启服务验证，验证通过后由用户手动 commit。
- 如果脚本提示补丁无法自动应用，停止自动处理；读取脚本输出的补丁路径、冲突文件和相关代码，给出 1-3 个解决方案让用户选择。
- 遇到数据库 schema、路由、权限、授权、配置、状态机等语义冲突，必须询问用户，不要擅自决定。
