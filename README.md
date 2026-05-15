# codex-cli-worktree

Codex CLI 的 Git worktree 并行开发辅助工具。

这个项目会安装一组 Codex Skills 和一个 Python 辅助脚本，用来简化多 Codex CLI 窗口并行开发时的 worktree 创建、合并、同步和清理流程。

> 说明：Codex App 已经有自己的 worktree 工作流。本项目主要面向 Codex CLI。

English documentation: [README.en.md](README.en.md)

## 功能

- 创建独立 Git worktree 任务目录。
- 切换预览时，先把主项目目录恢复干净，再把某个任务的改动复制过来看效果，不污染其他任务。
- 合并任务时，先把主项目目录恢复干净，再把任务改动复制回主项目目录，但不自动 commit。
- 查看当前窗口任务、恢复预览、同步、清理 worktree 任务。
- 任务状态按仓库隔离保存到 `~/.codex-cli-worktree/state/`，不写入业务项目仓库。
- 安装 Codex Skills 到 `~/.agents/skills/codex-cli-worktree/`。
- 幂等更新 `~/.codex/AGENTS.md` 中的通用规则块。

## 适用场景

这个工具适合在同一个 Git 仓库里同时推进多个 Codex CLI 任务，例如：

- 一个主任务正在改后端接口，同时另一个 Codex CLI 会话修复前端样式。
- 你想让多个 Codex CLI 会话互不影响地改代码，但最终都回到主项目目录统一验证和 commit。
- 你希望任务目录隔离，避免一个会话的临时修改阻塞另一个会话。
- 你需要在多个任务之间来回切换预览效果，但暂时不想把某个任务作为最终合并结果。

它不负责启动服务、运行长期进程或自动 commit。主项目目录是可重置的统一调试槽，只用于创建任务、切换预览、合并任务、同步任务、用户手动验证和用户手动 commit；任务 worktree 目录用于具体开发。

## 要求

- Codex CLI，且支持 Skills。
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
skills/codex-cli-worktree/worktree-*/SKILL.md -> ~/.agents/skills/codex-cli-worktree/worktree-*/SKILL.md
scripts/worktree-task.py -> ~/.agents/skills/codex-cli-worktree/scripts/worktree-task.py
```

并创建：

```text
~/.codex-cli-worktree/state/
```

同时追加或更新：

```text
~/.codex/AGENTS.md
```

安装后需要重启 Codex CLI，新的 Skills 才会加载。

## 怎么使用

安装并重启 Codex CLI 后，在聊天输入框里直接输入 skill 名称即可，例如：

```text
$worktree-list
$worktree-new 修复登录跳转
$worktree-switch 修复登录跳转
$worktree-merge 修复登录跳转
```

`$worktree-*` 是 Codex Skill mention，不是 shell 命令，也不是旧版 `/worktree-*` 斜杠命令。输入 `$worktree-` 后可以用 Codex 的补全选择具体 skill。

任务名可以使用中文或空格，但不能以 `-` 开头，避免和 `--all`、`--clear` 等命令选项冲突。命令中的 `<任务名>` 表示你自己起的任务名称，例如 `修复登录跳转`。

## 卸载

```bash
python3 uninstall.py
```

卸载脚本会删除已安装的 Skills 和 `~/.codex/AGENTS.md` 中的规则块，并询问是否保留历史任务状态。

## 升级

```bash
git pull
python3 install.py
```

升级后同样需要重启 Codex CLI。

## 命令说明

除特别说明外，建议在主项目目录打开 Codex CLI 后输入这些 skill。

| 输入 | 执行位置 | 作用 |
| --- | --- | --- |
| `$worktree-new <任务名>` | 主项目目录 | 创建新的任务 worktree 和任务分支。 |
| `$worktree-list` | 主项目目录，任务目录也可 | 查看当前 Git 仓库的 worktree 任务。 |
| `$worktree-info <任务名>` | 主项目目录，任务目录也可 | 查看指定任务的状态、分支和任务目录，并输出一行继续开发命令。 |
| `$worktree-current` | 主项目目录，任务目录也可 | 查看当前窗口对应任务；在主项目目录查看当前是 switch 预览、主线基线还是未提交改动状态。 |
| `$worktree-switch <任务名>` | 主项目目录 | 先把主项目目录恢复干净，再把任务目录里的改动复制过来用于验证，不反向同步、不自动 commit。 |
| `$worktree-switch --clear` | 主项目目录 | 清除当前 switch 预览，把主项目目录恢复到当前提交并清理新增文件。 |
| `$worktree-merge <任务名>` | 主项目目录 | 先把主项目目录恢复干净，再把任务目录里的改动复制到主项目目录，不自动 commit。 |
| `$worktree-sync <任务名>` | 主项目目录 | 把主项目最新提交带到指定任务目录，类似在任务目录拉取主线；有冲突会停止。 |
| `$worktree-sync --all` | 主项目目录 | 把主项目最新提交带到所有任务目录；无法自动同步的任务会停止并在汇总中列出。 |
| `$worktree-end <任务名>` | 主项目目录 | 清理任务 worktree、任务分支和任务状态。如果任务仍有未合并改动，会停止。 |
| `$worktree-help` | 任意 Git 项目目录 | 查看命令帮助。 |

## 推荐流程

假设你要做一个任务叫 `修复登录跳转`：

1. 在主项目目录打开 Codex CLI。
2. 输入 `$worktree-new 修复登录跳转`。
3. Codex 会创建一个任务 worktree，并输出任务目录。
4. 在输出的任务目录里打开新的 Codex CLI。
5. 在任务目录开发、改文件、跑必要的短命令；不要在任务目录启动长期运行的项目服务。
6. 需要临时看效果时，回到主项目目录输入 `$worktree-switch 修复登录跳转`，然后手动启动服务或运行验证命令。
7. 如果要切换看另一个任务，直接输入 `$worktree-switch 另一个任务名`；工具会先确认主项目目录只有上一轮预览改动，再恢复干净并切换。
8. 开发完成后，回到主项目目录输入 `$worktree-merge 修复登录跳转`。
9. 合并成功后，在主项目目录手动启动服务或运行验证命令。
10. 验证通过后，由你手动 `git commit`。
11. 主项目有新提交后，可输入 `$worktree-sync --all` 把最新提交带到其他任务目录；有冲突的任务会停止并输出处理建议。
12. 输入 `$worktree-end 修复登录跳转` 清理任务。

如果新会话忘记任务目录，可以在主项目目录输入 `$worktree-info 修复登录跳转` 查看。它只负责查询任务信息，不会自动切换当前 Codex CLI 会话目录；如果要继续开发，使用输出的 `cd ... && codex` 命令打开任务目录的新 Codex CLI。

如果当前窗口忘记自己在哪个任务，可以输入 `$worktree-current`。它在任务目录会显示任务名；在主项目目录会显示当前是 switch 预览状态、主线基线状态，还是存在未提交改动。

如果主项目目录有新的提交，需要带到任务目录，可以在主项目目录输入 `$worktree-sync 修复登录跳转` 或 `$worktree-sync --all`。执行 sync 前主项目目录必须没有未提交改动；如果自动同步会覆盖任务成果，工具会停止。

## 状态和生成文件

任务状态按仓库保存到：

```text
~/.codex-cli-worktree/state/<repo-id>/
```

任务 worktree 默认创建在仓库旁边：

```text
../<repo-name>.worktrees/<task-slug>/
```

状态文件只保存在本机，不会写入业务项目仓库。

## 安全约束

- 不自动 commit。
- `$worktree-switch` 只用于临时预览，不更新任务基线、不反向同步任务 worktree。
- `$worktree-switch` 会在主项目目录干净或等于已记录的 switch 预览时，自动把主项目目录恢复到当前提交并清理新增文件后复制任务改动；遇到无法确认来源的未提交改动会停止。
- `$worktree-merge` 会在复制任务改动前恢复并清理主项目调试槽，不自动 commit。
- 主项目目录有无法确认来源的未提交改动时，不执行 switch/merge/sync。
- sync 只负责把主项目最新提交带到任务目录；遇到冲突或可能覆盖任务成果时停止，不提供强制覆盖参数。
- 任务 worktree 有未合并改动时，不执行 end。
- 遇到数据库 schema、路由、权限、授权、配置、状态机等语义冲突时，Codex 应停止并让用户决定。
- 不自动启动项目服务。

## 许可证

MIT
