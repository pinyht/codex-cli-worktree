#!/usr/bin/env python3
import re
import shutil
from pathlib import Path


VERSION = "16"
BEGIN = "<!-- codex-worktree-rules:start -->"
END = "<!-- codex-worktree-rules:end -->"
SKILL_BUNDLE_NAME = "codex-cli-worktree"
COMMANDS = [
    "worktree-list",
    "worktree-new",
    "worktree-switch",
    "worktree-current",
    "worktree-status",
    "worktree-merge",
    "worktree-sync",
    "worktree-take-sql",
    "worktree-push-sql",
    "worktree-end",
    "worktree-info",
    "worktree-help",
]

RULE_BLOCK = f"""{BEGIN}
## 通用 worktree 并行开发规则

版本：{VERSION}

- worktree 命令由用户级 Codex Skills 和脚本提供：
  - Skills：`~/.agents/skills/codex-cli-worktree/worktree-*/SKILL.md`
  - 脚本：`~/.agents/skills/codex-cli-worktree/scripts/worktree-task.py`
  - 状态：`~/.codex-cli-worktree/state/`
- 每个 Skill 目录都包含 `agents/openai.yaml`，设置 `allow_implicit_invocation: false`。这些命令只能由用户手动输入 `$worktree-*` 触发，Codex 不得自行调用，也不得用直接执行脚本、git 命令、复制文件、stash 等方式复刻流程。
- 常用命令：
  - `$worktree-new 任务名`：在主项目目录创建独立 worktree 任务目录和任务分支，默认目录为 `../<repo-name>.codex-worktrees/`。
  - `$worktree-switch 任务名`：先把主项目目录恢复到当前提交，再把任务目录里的改动临时复制过来用于验证，不自动 commit；任务分支有主线没有的提交时停止。
  - `$worktree-switch --clear`：清除当前 switch 预览，把主项目目录恢复到当前提交并清理新增文件。
  - `$worktree-current`：查看当前窗口对应的任务名，或查看主项目目录是否处于 switch 预览/主线基线状态。
  - `$worktree-status`：在当前窗口所在 Git 仓库执行 `git status --short --branch --untracked-files=all`，查看未提交文件。
  - `$worktree-merge 任务名`：先把主项目目录恢复到当前提交，再把任务目录里的改动三方合并回主项目目录，带出任务会话记忆，不自动 commit。
  - `$worktree-sync 任务名`：把主项目最新提交带到任务目录，效果类似在任务目录拉取主线；若任务本地改动已被主项目吸收，会自动把任务目录重置对齐到主线。
  - `$worktree-sync --all`：把主项目最新提交带到所有可同步的任务目录；无法自动同步的任务会停止并输出处理建议，任一任务失败时非零退出；已被主线吸收的任务会自动对齐。
  - `$worktree-take-sql 任务名 SQL文件...`：把任务 worktree 中新增的 SQL 文件拿到主项目目录，并从任务 worktree 删除，便于主目录先 review、commit 再同步回任务。
  - `$worktree-push-sql 任务名 SQL文件...`：把任务 worktree 中新增的 SQL 文件拿到主项目目录并删除任务副本，自动 add、commit、push，再把本次 SQL 文件同步到各任务并切换到该任务预览。
  - `$worktree-end 任务名`：清理任务 worktree、任务分支和本地状态记录；任务分支有主线没有的提交或仍有未合并改动时停止。
  - `$worktree-end 任务名 --force`：跳过任务分支提交和剩余改动检查并强制清理任务；仅在确认任务 worktree 剩余差异可以放弃时使用。
  - `$worktree-list`：查看所有 worktree 任务。
  - `$worktree-info 任务名`：查看指定任务的状态、分支和任务目录。
  - `$worktree-help`：查看命令帮助。
- `$worktree-new`、`$worktree-switch`、`$worktree-merge`、`$worktree-sync`、`$worktree-take-sql`、`$worktree-push-sql`、`$worktree-end` 必须在主项目目录执行；`$worktree-list`、`$worktree-info`、`$worktree-current`、`$worktree-status` 可在主项目目录或任务 worktree 执行。
- 主项目目录是可重置的统一调试槽，只用于创建任务、切换预览、合并任务、同步任务、用户运行服务验证和提交；任务目录用于具体开发和测试。新任务 worktree 默认创建在仓库同级的 `../<repo-name>.codex-worktrees/`。
- worktree 命令不得自动启动任何项目服务。
- 任务名必须是可直接复制到 `$worktree-switch 任务名` 的单个参数，不得包含空格、Tab、换行或路径非法字符，且不能以 `-` 开头或结尾。
- `$worktree-switch` 只用于预览任务效果；主项目目录干净或等于已记录的 switch 预览时，会自动恢复到当前提交并清理新增文件后复制任务改动；遇到无法确认来源的未提交改动必须停止；如果任务分支上有主线没有的提交，必须停止并提示用户按脚本输出的 `git reset --soft <提交>` 在任务目录恢复；如果 switch 因沙箱或文件系统权限无法写入主项目目录或 Git 索引（例如 `.git/index.lock: Read-only file system`、`Permission denied`）而失败，Codex 必须用同一命令重新执行并申请 `require_escalated` 提权。
- `$worktree-merge` 不得自动 commit；执行前主项目目录必须干净或等于已记录的 switch 预览，脚本会先恢复并清理主项目调试槽，再把任务改动三方合并到主项目目录；如果任务分支上有主线没有的提交，必须停止并提示用户按脚本输出的 `git reset --soft <提交>` 在任务目录恢复；遇到 Git 合并冲突时脚本保留冲突状态并输出基础分析，随后 Codex 必须读取冲突文件、三方版本和本次合并完整改动范围，检索相关路由、菜单、API、权限、配置、schema、测试和文档，给出 AI 语义级整体修复方案供用户选择，用户确认后再修改文件解决冲突。
- `$worktree-merge` 成功后，脚本会带出任务目录会话中的用户要求、最后总结和会话 ID；Codex 应把这些内容和主项目 `git diff` 一起用于后续提交说明。用户明确要求提交时，Codex 依据任务会话记忆和主项目 diff 写提交信息并执行 `git add -A && git commit`；用户也可能自己手动提交并自己写说明，此时不要重复提交。
- `$worktree-sync` 执行前主项目目录必须没有未提交改动；同步只把主项目最新提交带到任务目录，若任务本地改动已被主项目吸收，可自动把任务目录重置对齐到主线；无法自动同步或会覆盖任务改动时必须停止，不得强制覆盖任务目录。`$worktree-sync --all` 有任一任务被阻止时脚本以非零退出码结束。
- `$worktree-take-sql` 只支持 `.sql` 文件，一次可指定多个；执行前主项目目录必须干净或等于已记录的 switch 预览，执行时只拿取任务 worktree 中新增且未合并的 SQL 文件，复制到主项目目录后删除任务 worktree 内对应文件，不自动 commit。
- `$worktree-push-sql` 只支持 `.sql` 文件，一次可指定多个；执行前主项目目录必须干净或等于已记录的 switch 预览，执行后会自动提交、推送，只把本次 SQL 文件同步到各任务并切换到该任务预览；遇到同路径 SQL 内容不一致时必须停止；提交信息格式为 `add SQL文件 SQL文件`。部分任务 SQL 同步失败时脚本以非零退出码结束。
- `$worktree-end` 清理前会检查任务 worktree 改动和任务分支提交；如果这些改动已包含在主项目当前提交中，可以直接清理，否则必须以非零退出码停止。`$worktree-end 任务名 --force` 会跳过任务分支提交和剩余改动检查并删除任务目录、任务分支和本地状态；仅在用户明确确认任务 worktree 剩余差异可以放弃时使用，不得用来替代 merge 或 review。
- 脚本以非零退出码表示操作被阻止或未完成（包括拒绝执行、合并冲突、同步失败、SQL 部分同步失败和 end 发现未合并改动）。遇到非零退出码时先向用户说明原因，不要自动重试，也不要用其他方式绕过约束；正常的空操作（没有任务、没有待合并改动）退出码为 0。
- 遇到业务冲突、数据库 schema、权限、路由、授权、配置、状态机冲突，必须先说明方案并询问用户。
- worktree 任务状态按仓库隔离保存在本地 `~/.codex-cli-worktree/state/`，不会提交到任何仓库。
{END}
"""


def copy_tree_files(src_dir, dst_dir, pattern):
    dst_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for src in sorted(src_dir.glob(pattern)):
        dst = dst_dir / src.name
        shutil.copy2(src, dst)
        copied.append(dst)
    return copied


def validate_skill(skill_dir):
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise SystemExit(f"缺少 Skill 定义: {skill_md}")
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SystemExit(f"SKILL.md frontmatter 缺失: {skill_md}")
    end = text.find("\n---", 3)
    if end == -1:
        raise SystemExit(f"SKILL.md frontmatter 未闭合: {skill_md}")
    frontmatter = text[4:end]
    if not re.search(r"(?m)^name:\s*\S", frontmatter):
        raise SystemExit(f"SKILL.md 缺少 name: {skill_md}")
    if not re.search(r"(?m)^description:\s*\S", frontmatter):
        raise SystemExit(f"SKILL.md 缺少 description: {skill_md}")

    policy = skill_dir / "agents" / "openai.yaml"
    if not policy.is_file():
        raise SystemExit(f"缺少显式调用策略: {policy}")
    policy_text = policy.read_text(encoding="utf-8")
    if not re.search(r"(?m)^\s*allow_implicit_invocation:\s*false\s*$", policy_text):
        raise SystemExit(f"必须设置 allow_implicit_invocation: false: {policy}")


def install_skill_bundle(source_root, target_bundle):
    source_skills = source_root / "skills" / SKILL_BUNDLE_NAME
    if not source_skills.is_dir():
        raise FileNotFoundError(f"缺少 skills 目录: {source_skills}")

    target_bundle.mkdir(parents=True, exist_ok=True)
    installed = []
    for command in COMMANDS:
        src = source_skills / command
        dst = target_bundle / command
        validate_skill(src)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        installed.append(dst / "SKILL.md")

    scripts_dst = target_bundle / "scripts"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    installed_scripts = copy_tree_files(source_root / "scripts", scripts_dst, "worktree-*.py")
    return installed, installed_scripts


def cleanup_legacy_install(home_codex):
    removed = 0
    legacy_prompts = home_codex / "prompts"
    if legacy_prompts.is_dir():
        for path in legacy_prompts.glob("worktree-*.md"):
            path.unlink()
            removed += 1

    legacy_script = home_codex / "scripts" / "worktree-task.py"
    if legacy_script.exists():
        legacy_script.unlink()
        removed += 1
    return removed


def update_agents(home_codex):
    agents = home_codex / "AGENTS.md"
    content = agents.read_text(encoding="utf-8") if agents.exists() else ""

    if BEGIN in content and END in content:
        before, rest = content.split(BEGIN, 1)
        _old, after = rest.split(END, 1)
        parts = []
        if before.strip():
            parts.append(before.rstrip())
        parts.append(RULE_BLOCK.rstrip())
        if after.strip():
            parts.append(after.lstrip())
        new_content = "\n\n".join(parts).rstrip() + "\n"
        changed = new_content != content
    else:
        sep = "\n\n" if content.strip() else ""
        new_content = content.rstrip() + sep + RULE_BLOCK.rstrip() + "\n"
        changed = True

    if changed:
        agents.write_text(new_content, encoding="utf-8")
        return "updated"
    return "unchanged"


def main():
    source_root = Path(__file__).resolve().parent
    home_codex = Path.home() / ".codex"
    home_agents = Path.home() / ".agents"
    target_bundle = home_agents / "skills" / SKILL_BUNDLE_NAME
    tool_state = Path.home() / ".codex-cli-worktree" / "state"
    home_codex.mkdir(parents=True, exist_ok=True)
    home_agents.mkdir(parents=True, exist_ok=True)

    skills, scripts = install_skill_bundle(source_root, target_bundle)
    legacy_removed = cleanup_legacy_install(home_codex)
    agents_status = update_agents(home_codex)
    tool_state.mkdir(parents=True, exist_ok=True)

    print("worktree Skills 已安装/更新。")
    print(f"skills: {len(skills)} 个 -> {target_bundle}")
    print(f"scripts: {len(scripts)} 个 -> {target_bundle / 'scripts'}")
    print(f"legacy cleanup: {legacy_removed} 个旧文件")
    print(f"AGENTS.md: {agents_status} -> {home_codex / 'AGENTS.md'}")
    print(f"state: {tool_state}")
    print("请重启 Codex CLI，让 Skills 生效。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
