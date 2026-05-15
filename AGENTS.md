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
  - `$worktree-status`
  - `$worktree-merge 任务名`
  - `$worktree-sync 任务名`
  - `$worktree-sync --all`
  - `$worktree-take-sql 任务名 SQL文件...`
  - `$worktree-push-sql 任务名 SQL文件...`
  - `$worktree-end 任务名`
  - `$worktree-list`
  - `$worktree-info 任务名`
  - `$worktree-help`
- 任务名必须是可直接复制到 `$worktree-switch 任务名` 的单个参数，不得包含空格、Tab、换行或路径非法字符，且不能以 `-` 开头或结尾。

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
- `$worktree-take-sql` 只用于把任务 worktree 中新增且未合并的 `.sql` 文件提前拿到主项目目录，并从任务 worktree 删除；不自动 commit。
- `$worktree-push-sql` 用于一键把任务 worktree 中新增且未合并的 `.sql` 文件提前提交到主线：拿到主项目目录、删除任务副本、自动 add/commit/push、sync --all，并切换到该任务预览。
- `$worktree-status` 只查看当前窗口所在 Git 仓库的 `git status --short --branch --untracked-files=all`，不修改任何文件。
- 遇到业务冲突、数据库 schema、权限、路由、授权、配置、状态机冲突，必须停止并让用户决定。
- 不要自动启动任何项目服务。
- 先不考虑 Windows 适配，避免引入复杂兼容逻辑。

## 迁移说明

- 要发布为独立仓库时，把本 `.codex` 目录整体复制出去，并把复制后的目录作为仓库根目录。
- 复制到新仓库后，可以删除不需要的本机状态目录，例如 `worktrees/`。
- 独立仓库根目录保留本文件，便于后续 Codex 迭代维护。
