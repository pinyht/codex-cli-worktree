## 项目定位

- 项目名：`codex-cli-worktree`。
- 这是 Codex CLI worktree 并行开发工具目录，可整体复制为独立仓库。
- 目标是把通用 worktree Skills 安装到 `~/.agents/skills/codex-cli-worktree/`，供任意 Git 项目复用。
- 当前目录应只包含通用工具，不放具体业务项目代码。

## 目录结构

- `install.py`：安装或更新 HOME 级 Codex worktree 命令。
- `uninstall.py`：卸载 HOME 级 Codex worktree Skills，并询问是否保留历史状态。
- `skills/`：Codex Skills，安装到 `~/.agents/skills/codex-cli-worktree/`。
- `scripts/`：命令执行脚本，安装到 `~/.agents/skills/codex-cli-worktree/scripts/`。
- `README.md`：默认中文说明。
- `README.en.md`：英文说明。
- `LICENSE`：MIT 许可证。

## 使用方式

- 首次安装或升级时，在本目录执行：

```bash
python3 install.py
```

- 安装后重启 Codex CLI，再在任意 Git 项目中使用：
  - `$worktree-new 任务名`
  - `$worktree-switch 任务名`
  - `$worktree-switch --clear`
  - `$worktree-current`
  - `$worktree-merge 任务名`
  - `$worktree-sync 任务名`
  - `$worktree-sync --all`
  - `$worktree-end 任务名`
  - `$worktree-list`
  - `$worktree-info 任务名`
  - `$worktree-help`

- 卸载时，在本目录执行：

```bash
python3 uninstall.py
```

## 开发约束

- 不再提供 `/worktree-install` 或自定义 slash prompt；安装和升级统一由 `install.py` 完成。
- 修改命令行为时，优先更新 `scripts/worktree-task.py`，Skills 只保留简洁的调用说明和安全约束。
- 修改通用行为规则时，必须同步更新 `install.py` 内的 `VERSION` 和 `RULE_BLOCK`，必要时同步更新中英文 README。
- `install.py` 必须幂等：重复执行不能破坏用户已有 `~/.codex/AGENTS.md`，只能替换标记块之间的内容。
- 本机任务状态必须按仓库隔离保存在 `~/.codex-cli-worktree/state/`，不得写入业务项目仓库。
- `$worktree-merge` 不得自动 commit；合并成功后必须反向同步到任务 worktree。
- 遇到业务冲突、数据库 schema、权限、路由、授权、配置、状态机冲突，必须停止并让用户决定。
- 不要自动启动任何项目服务。
- 先不考虑 Windows 适配，避免引入复杂兼容逻辑。

## 迁移说明

- 要发布为独立仓库时，把本 `.codex` 目录整体复制出去，并把复制后的目录作为仓库根目录。
- 复制到新仓库后，可以删除不需要的本机状态目录，例如 `worktrees/`。
- 独立仓库根目录保留本文件，便于后续 Codex 迭代维护。
