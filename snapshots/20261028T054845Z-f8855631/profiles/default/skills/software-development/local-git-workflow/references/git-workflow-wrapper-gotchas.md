# Git Workflow Wrapper Gotchas

## Auto-stage behavior matters

The local wrapper at `/Users/miqui/development/scripts/git-workflow.sh` only auto-runs `git add -A` when nothing is already staged.

Implication:
- if the index is empty, it may stage more than intended
- if some deletions or edits are already staged, new untracked files are **not** auto-added

Example failure mode:
- staged deletions for tracked `__pycache__` files
- created a new `.gitignore`
- ran `git-workflow.sh change ...`
- commit included only the deletions; `.gitignore` stayed untracked locally

## Safe preflight

Before `init` or `change`:

1. run `git status --short`
2. check whether the index is empty or partially staged
3. if you have a mixed set of deletions/edits plus new files, explicitly stage the intended allowlist first
4. then invoke the wrapper

## PR-creation transient failures

A `change` run may succeed through branch creation, commit, and push, then fail while opening the PR due to a transient GitHub API issue (for example GraphQL `502 Bad Gateway`).

Treat this as:
- wrapper partially succeeded
- branch may already be pushed
- inspect read-only state and report exactly what remains local
- do **not** bypass the wrapper with raw `gh pr create` or other workaround paths

Capture for the user:
- branch name
- commit status
- what remains uncommitted locally
- wrapper stderr/output
