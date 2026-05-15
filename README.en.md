# codex-cli-worktree

Git worktree workflow helpers for Codex CLI.

This project installs a set of Codex Skills and a Python helper script to make multi-window Codex CLI development with Git worktrees easier to manage.

> Note: Codex App has its own worktree workflow. This project targets Codex CLI.

中文说明: [README.md](README.md)

## Features

- Create isolated Git worktree task directories.
- Merge task changes back into the main project directory without auto-committing.
- Sync the final merged result back into the task worktree, so follow-up work does not continue from stale code.
- List, inspect, sync, and clean up worktree tasks.
- Store per-repository task state under `~/.codex-cli-worktree/state/`.
- Install Codex Skills into `~/.agents/skills/codex-cli-worktree/`.
- Idempotently update a managed rules block in `~/.codex/AGENTS.md`.

## Use cases

Use this tool when you want multiple Codex CLI sessions to work in the same Git repository without stepping on each other's files, for example:

- One Codex CLI session changes backend APIs while another fixes frontend UI.
- You want isolated task directories, but still merge everything back into the main project directory for verification and commit.
- You want to keep temporary task edits from blocking another session.

The tool does not start services, run long-lived processes, or commit automatically. The main project directory is for creating tasks, merging tasks, manual verification, and manual commits. Task worktree directories are for implementation work.

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
$worktree-merge fix login redirect
```

`$worktree-*` is a Codex Skill mention, not a shell command and not the old `/worktree-*` slash command. Type `$worktree-` and use Codex completion to choose a skill.

`<task name>` is the human-readable task name you choose, for example `fix login redirect`.

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
| `$worktree-merge <task name>` | Main project directory | Apply task changes to the main project directory without committing, then sync the final merged result back to the task worktree. |
| `$worktree-sync <task name>` | Main project directory | Sync the current main project files back to the task worktree. This stops if the task worktree has unmerged changes. |
| `$worktree-end <task name>` | Main project directory | Remove the task worktree, task branch, and task state. This stops if the task still has unmerged changes. |
| `$worktree-help` | Any Git project directory | Show command help. |

## Recommended workflow

Suppose the task is named `fix login redirect`:

1. Open Codex CLI in the main project directory.
2. Type `$worktree-new fix login redirect`.
3. Codex creates a task worktree and prints the task directory.
4. Open a separate Codex CLI session in that task directory.
5. Develop in the task directory. Run only necessary short-lived commands there; do not start long-running project services.
6. When implementation is done, return to Codex CLI in the main project directory.
7. Type `$worktree-merge fix login redirect`.
8. After merge succeeds, manually start services or run verification commands from the main project directory.
9. Commit manually when satisfied.
10. Type `$worktree-end fix login redirect` to clean up.

If a new session needs to find the task directory, type `$worktree-info fix login redirect` from the main project directory. It only prints task information; it does not switch the current Codex CLI session directory automatically. To continue development, use the printed `cd ... && codex` command to open a new Codex CLI in the task directory.

If the main project directory changed and you need to refresh the task worktree, type `$worktree-sync fix login redirect` from the main project directory. If the task worktree has unmerged changes, the tool stops instead of overwriting task work.

## State and generated files

Task state is stored per repository under:

```text
~/.codex-cli-worktree/state/<repo-id>/
```

Worktree directories are created next to the repository:

```text
../<repo-name>.worktrees/<task-slug>/
```

Patch files used during merge or sync are saved under the repository-specific state directory for troubleshooting.

## Safety model

- The tool does not auto-commit.
- The tool refuses to merge when the main project directory has uncommitted changes.
- The tool refuses to sync/end when the task worktree has unmerged changes.
- Codex should stop and ask before resolving semantic conflicts such as database schemas, routing, permissions, authorization, configuration, or state machines.
- The tool does not start project services.

## License

MIT
