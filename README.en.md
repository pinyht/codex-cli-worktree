# codex-cli-worktree

Git worktree workflow helpers for Codex CLI.

This project installs a set of Codex Skills and a Python helper script to make multi-window Codex CLI development with Git worktrees easier to manage.

> Note: Codex App has its own worktree workflow. This project targets Codex CLI.

中文说明: [README.md](README.md)

## Features

- Create isolated Git worktree task directories.
- Restore the main project directory to a clean state, then copy a task's changes into it for preview without contaminating other tasks.
- Restore the main project directory to a clean state, then three-way merge task changes back into it without auto-committing; when conflicts occur, Codex analyzes the conflict context and the full merge change set, then proposes semantic AI-assisted fixes. When merge succeeds, the task worktree is automatically aligned to the mainline so later syncs do not keep replaying old differences.
- Take newly added SQL migration files from a task into the main project directory so they can be reviewed, committed, and synced back before the rest of the task is merged.
- Push task SQL migrations into mainline in one command, sync those SQL files to all tasks, and switch back to that task preview.
- List, inspect the current window, clear previews, sync, and clean up worktree tasks.
- Inspect the current Git worktree status from inside Codex CLI, making uncommitted files and SQL paths easy to see.
- New task worktree directory names include the full task name, making multiple Codex CLI windows easier to distinguish.
- Store per-repository task state under `~/.codex-cli-worktree/state/`.
- Install Codex Skills into `~/.agents/skills/codex-cli-worktree/`.
- Idempotently update a managed rules block in `~/.codex/AGENTS.md`.

## Use cases

Use this tool when you want multiple Codex CLI sessions to work in the same Git repository without stepping on each other's files, for example:

- One Codex CLI session changes backend APIs while another fixes frontend UI.
- You want isolated task directories, but still merge everything back into the main project directory for verification and commit.
- You want to keep temporary task edits from blocking another session.
- You need to preview multiple tasks one by one in the main project directory before deciding which task is ready to merge.

The tool does not start services, run long-lived processes, or commit automatically. The main project directory is a resettable shared debug slot for creating tasks, switching previews, merging tasks, syncing tasks, manual verification, and manual commits. Task worktree directories are for implementation work.

## Requirements

- Codex CLI with Skills support.
- Python 3.
- Git.
- Linux or macOS. Windows is not supported yet.

## Installation

Clone this repository, then run:

```bash
python3 install.py
```

The installer copies:

```text
skills/codex-cli-worktree/worktree-*/SKILL.md -> ~/.agents/skills/codex-cli-worktree/worktree-*/SKILL.md
scripts/worktree-task.py -> ~/.agents/skills/codex-cli-worktree/scripts/worktree-task.py
```

It also creates:

```text
~/.codex-cli-worktree/state/
```

and adds or updates:

```text
~/.codex/AGENTS.md
```

Restart Codex CLI after installation so the new Skills are loaded.

## How to use

After installing and restarting Codex CLI, type the skill name in the chat input:

```text
$worktree-list
$worktree-new fix login redirect
$worktree-status
$worktree-switch fix login redirect
$worktree-merge fix login redirect
$worktree-take-sql fix login redirect migrations/18.sql
$worktree-push-sql fix login redirect migrations/18.sql
```

`$worktree-*` is a Codex Skill mention, not a shell command and not the old `/worktree-*` slash command. Type `$worktree-` and use Codex completion to choose a skill.

`<task name>` is the human-readable task name you choose, for example `fix-login`. Task names may contain Chinese characters, English letters, digits, `-`, `_`, and `.`, but must be a single argument: no spaces, tabs, newlines, path separators, or path-invalid characters such as `: * ? " < > |`. Task names must not start or end with `-`, so they cannot conflict with options such as `--all` and the generated worktree directory remains tidy.

## Uninstall

```bash
python3 uninstall.py
```

The uninstaller removes the installed Skills and the managed rules block in `~/.codex/AGENTS.md`, then asks whether to keep historical task state and patch records.

## Upgrade

```bash
git pull
python3 install.py
```

Restart Codex CLI after upgrading.

## Commands

Unless noted otherwise, open Codex CLI in the main project directory before using these skills.

| Input | Where to run | What it does |
| --- | --- | --- |
| `$worktree-new <task name>` | Main project directory | Create a new task worktree and task branch. |
| `$worktree-list` | Main project directory; task directories also work | List worktree tasks for the current Git repository. |
| `$worktree-info <task name>` | Main project directory; task directories also work | Show the task status, branch, task directory, and a one-line command to continue development. |
| `$worktree-current` | Main project directory; task directories also work | Show the current task for this window, or whether the main project directory is in a switch preview, baseline, or uncommitted state. |
| `$worktree-status` | Main project directory; task directories also work | Show `git status --short --branch --untracked-files=all` for the current Git repository, useful for checking uncommitted files and SQL paths. |
| `$worktree-switch <task name>` | Main project directory | Restore the main project directory, then copy the task directory's changes into it for preview. It does not sync back or commit. |
| `$worktree-switch --clear` | Main project directory | Clear the current switch preview, restore the main project directory to the current commit, and remove preview-created files. |
| `$worktree-merge <task name>` | Main project directory | Restore the main project directory, then three-way merge the task directory's changes into it without committing; conflicts are then analyzed and guided by Codex. |
| `$worktree-sync <task name>` | Main project directory | Bring the main project's latest commit into one task directory, similar to pulling mainline in that task directory. If the task's local changes have already been absorbed by main, the task directory is automatically reset to the mainline baseline. |
| `$worktree-sync --all` | Main project directory | Bring the main project's latest commit into all task directories. Tasks that cannot be updated automatically are stopped and listed in the summary; tasks whose local changes have already been absorbed by main are automatically aligned. |
| `$worktree-take-sql <task name> <sql...>` | Main project directory | Take newly added `.sql` files from a task worktree into the main project directory and delete them from the task worktree. Multiple SQL files are supported. It does not commit. |
| `$worktree-push-sql <task name> <sql...>` | Main project directory | Take newly added `.sql` files from a task worktree, delete the task copies, auto add/commit/push, sync those SQL files to all tasks, then switch to that task preview. |
| `$worktree-end <task name>` | Main project directory | Remove the task worktree, task branch, and task state. This stops if the task still has unmerged changes. |
| `$worktree-end <task name> --force` | Main project directory | Force cleanup. Use only after you confirm the task worktree's remaining differences can be discarded. |
| `$worktree-help` | Any Git project directory | Show command help. |

## Recommended workflow

Suppose the task is named `fix login redirect`:

1. Open Codex CLI in the main project directory.
2. Type `$worktree-new fix login redirect`.
3. Codex creates a task worktree and prints the task directory.
4. Open a separate Codex CLI session in that task directory.
5. Develop in the task directory. Run only necessary short-lived commands there; do not start long-running project services.
6. When you need to preview the task, return to the main project directory and type `$worktree-switch fix login redirect`, then manually start services or run verification commands.
7. To preview another task, type `$worktree-switch another task`; the tool first checks that the main project directory only contains the previous preview, then restores it cleanly and switches tasks.
8. When implementation is done, return to Codex CLI in the main project directory and type `$worktree-merge fix login redirect`. When merge succeeds, the task worktree is automatically aligned to the mainline.
9. If conflicts occur, the tool lists conflicted files and leaves the conflict state in place. Codex then reads the conflicted files, base/main/task versions, and the full merge change set; it also searches related routes, menus, APIs, permissions, config, schema, tests, and docs before proposing semantic AI-assisted fixes. You can also choose all-manual handling.
10. After merge succeeds or conflict handling is complete, manually start services or run verification commands from the main project directory.
11. Commit manually when satisfied.
12. After the main project has a new commit, type `$worktree-sync --all` to bring that commit into other task directories. Tasks with conflicts or changes that might be overwritten stop and print advice; tasks already absorbed by main are automatically aligned.
13. Type `$worktree-end fix login redirect` to clean up. If a conflict was resolved through semantic merging and the main project has already been committed with a clean worktree, but end still reports unmerged task changes, inspect the remaining differences first. Only after confirming the task worktree's original leftover differences can be discarded should you explicitly ask Codex to use `$worktree-end fix login redirect --force`.

If a new session needs to find the task directory, type `$worktree-info fix login redirect` from the main project directory. It only prints task information; it does not switch the current Codex CLI session directory automatically. To continue development, use the printed continue-development command to open a new Codex CLI in the task directory.

New task worktree directory names include the full task name, for example `task-channel-config-31a1f97b` or `task-频道配置-31a1f97b`. Git branch names still use ASCII-safe slugs to avoid compatibility issues with non-ASCII branch names.

If you forget which task the current window belongs to, type `$worktree-current`. In a task directory it prints the task name. In the main project directory it prints whether you are in a switch preview, the mainline baseline, or an uncommitted state.

To check uncommitted files without leaving Codex CLI, type `$worktree-status`. It prints the current Git repository path and `git status --short --branch --untracked-files=all`; newly generated SQL appears with relative paths, for example `?? migrations/18.sql`.

If the main project directory has a new commit that task directories should receive, type `$worktree-sync fix login redirect` or `$worktree-sync --all` from the main project directory. The main project directory must have no uncommitted changes before sync runs. If the task's local changes have already been absorbed by main, the tool automatically resets the task directory to the mainline baseline. If updating a task would overwrite task work, the tool stops.

If a task generated database migration SQL but the main project directory should control migration order, run this from the main project directory:

```text
$worktree-take-sql fix login redirect migrations/18.sql migrations/19.sql
```

This command only accepts `.sql` files. It copies those newly added SQL files from the task worktree into the main project directory and deletes the matching files from the task worktree. It does not commit. Review and commit the SQL in the main project directory, then run `$worktree-sync fix login redirect` so the task worktree receives the SQL from mainline.

If you want a one-command flow that pushes SQL into mainline and returns to the task preview, run:

```text
$worktree-push-sql fix login redirect migrations/18.sql migrations/19.sql
```

It runs: take SQL, delete the task SQL copies, `git add`, `git commit -m "add migrations/18.sql migrations/19.sql"`, `git push`, sync those SQL files to all tasks, then `$worktree-switch fix login redirect`. It does not run a full `$worktree-sync --all`, so unrelated local task changes do not block SQL-number synchronization. If push fails, the target task cannot receive the SQL files, or a task already has a same-path SQL file with different content, the command stops and prints the reason.

## State and generated files

Task state is stored per repository under:

```text
~/.codex-cli-worktree/state/<repo-id>/
```

Worktree directories are created next to the repository:

```text
../<repo-name>.worktrees/task-<task-name>-<hash>/
```

State files are stored only on your machine and are not written into the project repository.

## Safety model

- The tool does not auto-commit.
- `$worktree-switch` is only a preview operation. It does not update the task baseline or sync anything back to the task worktree.
- `$worktree-switch` restores the main project directory to the current commit and removes preview-created files before copying task changes when the main project directory is clean or equals the recorded switch preview. Unknown uncommitted changes stop the operation.
- `$worktree-merge` restores and cleans the main project debug slot before applying task changes with Git three-way merge. It does not auto-commit. When conflicts occur, the script leaves the conflict state in place and prints basic analysis. Codex then reads the conflicted files, base/main/task versions, and the full merge change set; it searches related routes, menus, APIs, permissions, config, schema, tests, and docs before proposing semantic AI-assisted fixes, and edits files only after you choose a plan. When merge succeeds, the task worktree is automatically aligned to the mainline.
- `$worktree-take-sql` only handles newly added, unmerged `.sql` files in a task worktree. It copies them into the main project directory, deletes the task copy, and does not auto-commit.
- `$worktree-push-sql` only handles newly added, unmerged `.sql` files in a task worktree. It auto-commits, pushes, and syncs only those SQL files to task worktrees, with the commit message format `add SQL SQL`.
- Unknown uncommitted changes in the main project directory stop switch/merge/sync/take-sql/push-sql.
- Sync only brings the main project's latest commit into task directories. It stops on conflicts or when it might overwrite task work, and has no force-overwrite option. If the task's local changes have already been absorbed by main, it automatically resets the task directory to the mainline baseline.
- The tool refuses to end a task when the task worktree has unmerged changes; if those changes are already contained in the current main project commit, cleanup is allowed.
- `$worktree-end <task name> --force` skips the remaining-change check and deletes the task worktree, task branch, and local state. Use it only when you have confirmed that the final result is already committed in the main project and the task worktree's remaining differences are just original leftovers from semantic conflict resolution or no longer needed work. Do not use it as a substitute for merge or review.
- Codex should stop and ask before resolving semantic conflicts such as database schemas, routing, permissions, authorization, configuration, or state machines.
- The tool does not start project services.

## License

MIT
