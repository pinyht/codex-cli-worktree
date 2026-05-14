# codex-cli-worktree

Codex CLI 的 Git worktree 并行开发辅助工具。

这个项目会安装一组 Codex CLI 自定义斜杠命令和一个 Python 辅助脚本，用来简化多 Codex CLI 窗口并行开发时的 worktree 创建、合并、同步和清理流程。

> 说明：Codex App 已经有自己的 worktree 工作流。本项目主要面向 Codex CLI。

English documentation: [README.en.md](README.en.md)

## 功能

- 创建独立 Git worktree 任务目录。
- 把任务改动合并回主项目目录，但不自动 commit。
- 合并后把最终结果反向同步回任务 worktree，避免后续继续基于旧代码开发。
- 查看、恢复、同步、清理 worktree 任务。
- 任务状态按仓库隔离保存到 `~/.codex/worktree-state/`，不写入业务项目仓库。
- 安装 Codex 自定义 prompts 到 `~/.codex/prompts/`。
- 幂等更新 `~/.codex/AGENTS.md` 中的通用规则块。

## 要求

- Codex CLI，且支持从 `~/.codex/prompts/` 加载自定义 prompts。
- Python 3。
- Git。
- Linux 或 macOS。暂不适配 Windows。

## 安装

克隆本仓库后执行：

```bash
python3 install.py
```

安装脚本会复制：

```text
prompts/worktree-*.md -> ~/.codex/prompts/
scripts/worktree-task.py -> ~/.codex/scripts/
```

并创建：

```text
~/.codex/worktree-state/
```

同时追加或更新：

```text
~/.codex/AGENTS.md
```

安装后需要重启 Codex CLI，新的斜杠命令才会加载。

## 升级

```bash
git pull
python3 install.py
```

升级后同样需要重启 Codex CLI。

## 命令

建议在主项目目录执行这些命令。

```text
/worktree-new <任务名>
```

创建新的任务 worktree 和任务分支。

```text
/worktree-merge <任务名>
```

把任务改动应用到主项目目录，不自动 commit，并把合并后的最终结果同步回任务 worktree。

```text
/worktree-sync <任务名>
```

把主项目当前文件同步回任务 worktree。如果任务 worktree 有未合并改动，会停止。

```text
/worktree-end <任务名>
```

清理任务 worktree、任务分支和任务状态。如果任务仍有未合并改动，会停止。

```text
/worktree-list
```

查看当前 Git 仓库的 worktree 任务。

```text
/worktree-resume <任务名>
```

输出任务目录和状态，方便新会话继续处理。

```text
/worktree-help
```

查看命令帮助。

## 推荐流程

1. 在主项目目录打开 Codex CLI。
2. 执行 `/worktree-new <任务名>`。
3. 在生成的任务目录里打开新的 Codex CLI。
4. 在任务目录开发，不启动长期运行的项目服务。
5. 回到主项目目录执行 `/worktree-merge <任务名>`。
6. 在主项目目录手动重启或运行服务验证效果。
7. 验证通过后手动 commit。
8. 执行 `/worktree-end <任务名>` 清理任务。

## 状态和生成文件

任务状态按仓库保存到：

```text
~/.codex/worktree-state/<repo-id>/
```

任务 worktree 默认创建在仓库旁边：

```text
../<repo-name>.worktrees/<task-slug>/
```

合并或同步时生成的补丁会保存在对应仓库的状态目录中，便于排查冲突。

## 安全约束

- 不自动 commit。
- 主项目目录有未提交改动时，不执行 merge。
- 任务 worktree 有未合并改动时，不执行 sync/end。
- 遇到数据库 schema、路由、权限、授权、配置、状态机等语义冲突时，Codex 应停止并让用户决定。
- 不自动启动项目服务。

## 许可证

MIT
