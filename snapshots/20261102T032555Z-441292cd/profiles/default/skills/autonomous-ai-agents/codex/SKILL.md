---
name: codex
description: "Delegate coding to OpenAI Codex CLI (features, PRs)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [claude-code, hermes-agent]
---

# Codex CLI

Delegate coding tasks to [Codex](https://github.com/openai/codex) via the Hermes terminal. Codex is OpenAI's autonomous coding agent CLI.

## When to use

- Building features
- Refactoring
- PR reviews
- Batch issue fixing

Requires the codex CLI and a git repository.

## Prerequisites

- Codex installed: `npm install -g @openai/codex`
- OpenAI auth configured: either an exported `OPENAI_API_KEY` or Codex OAuth/API-key credentials from the Codex CLI login flow
- If loading the key from a dotenv file, make sure it is exported to child processes. `source ~/.hermes/.env` alone is not enough in bash; use `set -a; source ~/.hermes/.env; set +a` or `export OPENAI_API_KEY=...`
- **Must run inside a git repository** — Codex refuses to run outside one
- Use `pty=true` in terminal calls — Codex is an interactive terminal app

For Hermes itself, `model.provider: openai-codex` uses Hermes-managed Codex
OAuth from `~/.hermes/auth.json` after `hermes auth add openai-codex`. For the
standalone Codex CLI, a valid CLI OAuth or API-key login may live under
`~/.codex/`; do not treat a missing `OPENAI_API_KEY` alone as proof that Codex
auth is missing.

If `OPENAI_API_KEY` is present and valid but `codex exec ...` still returns
401s that mention missing bearer authentication, suspect one of two causes:
1. the key was loaded from a dotenv file but not exported to the Codex child
   process; or
2. this Codex install expects credentials to be registered with `codex login
   --with-api-key` rather than relying on env-only auth.
Check `codex login --help` and `codex login status` before concluding the key
itself is bad.

## Manual API-Key Setup

For installs where env-only auth is flaky or you want an explicit Codex-side
login state, register the key with Codex directly:

```bash
export OPENAI_API_KEY='your_api_key_here'
printenv OPENAI_API_KEY | codex login --with-api-key
codex login status
```

If the key already lives in a dotenv file, export it before invoking Codex:

```bash
set -a
source ~/.hermes/.env
set +a
printenv OPENAI_API_KEY | codex login --with-api-key
codex login status
```

Minimal smoke test after login:

```bash
TMP=$(mktemp -d)
cd "$TMP"
git init
codex exec 'Reply with exactly READY and nothing else.'
```

## Troubleshooting

- `401 Unauthorized` with `Missing bearer or basic authentication in header`
  after `codex exec` does not automatically mean the API key is invalid.
  First verify the key separately against OpenAI, then verify export behavior:
  `set -a; source ~/.hermes/.env; set +a; env | grep '^OPENAI_API_KEY='`.
- Check `codex login status` before concluding setup is broken. It can confirm
  whether Codex is using its own stored API-key login even when env-based auth
  behavior is ambiguous.
- If the key is valid but Codex still emits the same 401, try `codex login
  --with-api-key` (reads the key from stdin) unless the user explicitly wants
  to avoid Codex's local credential store.
- For a minimal smoke test, use a temp git repo and ask for a fixed literal
  response: `TMP=$(mktemp -d) && cd "$TMP" && git init && codex exec 'Reply
  with exactly READY and nothing else.'`
- `source ~/.hermes/.env` without `export` can fool manual verification: the
  shell sees the variable, but child processes like Codex do not.
- If the user asks for a manual setup recipe, prefer the exact commands above
  instead of describing the flow abstractly.

Reference: `references/auth-debugging.md`

## One-Shot Tasks

```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work (Codex needs a git repo):
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## Background Mode (Long Tasks)

```
# Start in background with PTY
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Codex asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes in workspace |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |

## PR Reviews

Clone to a temp directory for safe review:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Parallel Issue Fixing with Worktrees

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Codex in each
terminal(command="codex --yolo exec 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="codex --yolo exec 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, pty=true)

# Monitor
process(action="list")

# After completion, push and create PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## Batch PR Reviews

```
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# Review multiple PRs in parallel
terminal(command="codex exec 'Review PR #86. First run git diff --stat origin/main...origin/pr/86 and git diff --name-only origin/main...origin/pr/86. Then inspect selected file diffs; do not load an unbounded PR diff unless the scoped review requires it.'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec 'Review PR #87. First run git diff --stat origin/main...origin/pr/87 and git diff --name-only origin/main...origin/pr/87. Then inspect selected file diffs; do not load an unbounded PR diff unless the scoped review requires it.'", workdir="~/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## Rules

1. **Always use `pty=true`** — Codex is an interactive terminal app and hangs without a PTY
2. **Git repo required** — Codex won't run outside a git directory. Use `mktemp -d && git init` for scratch
3. **Use `exec` for one-shots** — `codex exec "prompt"` runs and exits cleanly
4. **`--full-auto` for building** — auto-approves changes within the sandbox
5. **Background for long tasks** — use `background=true` and monitor with `process` tool
6. **Don't interfere** — monitor with `poll`/`log`, be patient with long-running tasks
7. **Parallel is fine** — run multiple Codex processes at once for batch work
