# Token-Efficient Git Inspection

Use this reference when a Git command's output will enter an agent, reviewer, or subagent context.

## Principle: summarize before patches

Git output is model input. Start with compact scope discovery, then request a patch only for selected files or a deliberately bounded review.

```bash
# Machine-stable working-tree state; add --branch only when branch/upstream state matters.
git status --porcelain=v1
git status --porcelain=v1 --branch

# Separate staged and unstaged scope before inspecting content.
git diff --cached --stat
git diff --cached --name-only
git diff --stat
git diff --name-only

# Inspect only selected paths after scope discovery.
git diff --cached -- path/to/file.py
git diff -- path/to/file.py
```

## Full patches are an escalation

A complete diff is appropriate only when the scope is deliberately small or a reviewer requires cross-file context. Do not emit it merely to discover what changed.

For multi-agent review, inspect `--shortstat` before distributing a patch. If the diff is oversized, stop and ask the user to narrow by file, directory, or commit instead of duplicating the full patch across agents.

## Preserve diagnostic semantics

Do not replace a `git diff | grep ...` security/diagnostic pipeline with `--stat`: the pipeline's observable output is already limited to matches. Do not add `--ff-only` or shallow clone flags solely for token savings, since those change Git behavior.

## Command-output details

- `--porcelain=v1` is stable and machine-readable. Use `-z` only in a real parser that handles NUL-separated paths; avoid it for ordinary agent-visible terminal output.
- `--no-pager` changes paging behavior, not output size, so it is not a token optimization.
- `--stat`, `--shortstat`, and `--name-only` serve different questions: per-file magnitude, total magnitude, and file identity.
