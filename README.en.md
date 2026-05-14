# codex-cli-worktree

Git worktree workflow helpers for Codex CLI.

This project installs a set of Codex CLI custom slash prompts and a Python helper script to make multi-window Codex CLI development with Git worktrees easier to manage.

> Note: Codex App has its own worktree workflow. This project targets Codex CLI.

中文说明: [README.md](README.md)

## Features

- Create isolated Git worktree task directories.
- Merge task changes back into the main project directory without auto-committing.
- Sync the final merged result back into the task worktree, so follow-up work does not continue from stale code.
- List, resume, sync, and clean up worktree tasks.
- Store per-repository task state under `~/.codex/worktree-state/`.
- Install Codex prompts into `~/.codex/prompts/`.
- Idempotently update a managed rules block in `~/.codex/AGENTS.md`.

## Requirements

- Codex CLI with custom prompts loaded from `~/.codex/prompts/`.
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
prompts/worktree-*.md -> ~/.codex/prompts/
scripts/worktree-task.py -> ~/.codex/scripts/
```

It also creates:

```text
~/.codex/worktree-state/
```

and adds or updates:

```text
~/.codex/AGENTS.md
```

Restart Codex CLI after installation so the new slash commands are loaded.

## Upgrade

```bash
git pull
python3 install.py
```

Restart Codex CLI after upgrading.

## Commands

Run these commands from the main project directory unless noted otherwise.

```text
/worktree-new <task name>
```

Create a new task worktree and task branch.

```text
/worktree-merge <task name>
```

Apply task changes to the main project directory without committing, then sync the final merged result back to the task worktree.

```text
/worktree-sync <task name>
```

Sync the current main project files back to the task worktree. This stops if the task worktree has unmerged changes.

```text
/worktree-end <task name>
```

Remove the task worktree, task branch, and task state. This stops if the task still has unmerged changes.

```text
/worktree-list
```

List worktree tasks for the current Git repository.

```text
/worktree-resume <task name>
```

Show the task directory and state so a new session can continue the task.

```text
/worktree-help
```

Show command help.

## Recommended workflow

1. Open Codex CLI in the main project directory.
2. Run `/worktree-new <task name>`.
3. Open a separate Codex CLI session in the generated task directory.
4. Develop in the task directory. Do not start long-running project services there.
5. Return to the main project directory and run `/worktree-merge <task name>`.
6. Manually restart or run the project from the main directory to verify the result.
7. Commit manually when satisfied.
8. Run `/worktree-end <task name>` to clean up.

## State and generated files

Task state is stored per repository under:

```text
~/.codex/worktree-state/<repo-id>/
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
