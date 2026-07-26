---
name: local-git-workflow
description: "Use when repository creation, pushes, branch publication, or pull-request workflows in this local environment must go through `/Users/miqui/development/scripts/git-workflow.sh` rather than raw git, gh, or API workarounds."
version: 1.0.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [git, github, workflow, local-environment, pull-requests]
    related_skills: [go-builder, github-pr-workflow, github-repo-management]
---

# Local Git Workflow

## Overview

This skill defines the mandatory GitHub write-side workflow for the current local environment. Repository creation, branch publication, pushes, and pull-request creation must use the wrapper script at `/Users/miqui/development/scripts/git-workflow.sh`.

This is an environment policy skill, not a general Git or GitHub best-practices guide. Use it whenever the task involves write-side GitHub actions from this machine.

## When to Use

- Creating a new repository that should be published to GitHub from this machine
- Publishing a branch or pushing changes to GitHub
- Opening a pull request
- Deciding whether a GitHub-side action may use raw `git`, `gh`, or API calls
- Verifying whether a project should be initialized with the wrapper script

Do not use this skill for read-only inspection such as `git status --porcelain=v1`, `git diff --stat`, `git log`, or local file review unless that inspection is directly supporting a write-side GitHub action.

## Mandatory Rule

For repository creation, pushes, branch publication, and pull-request creation, you must use:

```bash
bash /Users/miqui/development/scripts/git-workflow.sh ...
```

Do not bypass this wrapper with:

- `git push`
- `gh repo create`
- `gh pr create`
- direct GitHub REST or GraphQL write calls
- any alternative script or workaround

If the wrapper fails, stop and surface the error. Do not retry with a bypass path.

## Workspace Location

When creating new repositories in this environment, place them under:

```text
/Users/miqui/development/
```

## Commands

### Wrapper behavior snapshot

The current `/Users/miqui/development/scripts/git-workflow.sh` implementation supports four subcommands:

- `init`
- `change`
- `update`
- `pr`

It does **not** expose a `--help` flag. Invoking `--help` currently returns an error like:

```text
[git-workflow] ERROR: Unknown command '--help'. Use: init | change | update | pr
```

Plan to call one of the supported subcommands directly instead of probing for help text first.

### `init`

Use once, when the repository has no prior commits and the initial scaffold is ready:

```bash
git init -b main
bash /Users/miqui/development/scripts/git-workflow.sh init "feat: initial project scaffold"
```

Use `init` only when `git log` is empty or unavailable because the repository has not been initialized with a first commit yet. The current wrapper also requires that you are already inside a local Git repository; without a prior `git init`, it fails with `Not inside a git repository.`

Current wrapper behavior during `init`:

- verifies GitHub connectivity via SSH first, then `gh` auth fallback
- auto-stages all changes with `git add -A` if nothing is already staged
- creates the initial commit
- creates a **public** GitHub repo named after the local directory if it does not already exist
- sets `origin` to the SSH remote `git@github.com:<user>/<repo>.git`
- pushes the current branch and sets upstream

### `change`

Use for all meaningful changes after the initial publication:

```bash
bash /Users/miqui/development/scripts/git-workflow.sh change "feat: add user authentication middleware"
```

Current wrapper behavior during `change`:

- creates a new branch before committing
- auto-generates the branch name from the commit message when no explicit branch name is supplied
- auto-stages all changes with `git add -A` if nothing is already staged
- commits, pushes the branch, and opens a pull request against `main`
- limits generated PR-body diff statistics to stay under GitHub's 65,536-character body limit

### `update`

Use when an existing non-`main` PR branch needs another commit, such as a CI/workflow fix. Do not use `change`: it creates a new branch and PR.

```bash
bash /Users/miqui/development/scripts/git-workflow.sh update "ci: trigger validation for every pull request"
```

Current wrapper behavior during `update`:

- verifies GitHub connectivity and that current non-`main` branch exists on `origin`
- stages all changes only when index is empty; stage an explicit allowlist for mixed worktrees
- commits and pushes the current branch, updating its existing PR
- does not create a second PR

### Snapshot-backed PR validation

For repositories that commit complete backup snapshots or other immutable historical artifacts, do **not** validate every historical artifact on each PR by default. That creates repeated warning noise and lets legacy validation debt obscure the artifact under review.

Use this design:

1. Keep the `pull_request` trigger so tests run for every PR lifecycle update.
2. Detect snapshot IDs changed by the PR using its base and head SHAs, for example by diffing `snapshots/*/MANIFEST.json` with a full checkout history.
3. Validate each changed snapshot ID individually; this is the PR gate.
4. Run an all-history audit only on a schedule or `workflow_dispatch`. If documented legacy debt makes that audit non-actionable, keep it visible but non-blocking until the baseline is repaired.
5. After wrapper publication, verify the remote branch SHA and watch the actual Actions run. A triggered workflow, a passing test job, and a passing artifact-validation job are distinct proofs.

Never suppress all secret scanning merely to make a PR green. Narrow a demonstrably over-broad detector with regression tests, preserve high-confidence detectors, and report only category/path/line—not the matched value.

### `pr`

Use only when `change` has already committed and pushed the current feature branch but PR creation did not complete, such as a transient GitHub failure or a formerly oversized generated PR body:

```bash
bash /Users/miqui/development/scripts/git-workflow.sh pr "feat: add caveman skill corpus snapshot"
```

Current wrapper behavior during `pr`:

- verifies GitHub connectivity
- requires a non-`main` branch that already exists on `origin`
- uses the supplied title, or the current commit subject when omitted
- opens the PR against `main` using the same bounded body generator as `change`

Do not use raw `gh pr create` to resume a partial-success publish. Use `pr` after inspecting the branch, pushed commit, and worktree.

- `feat:`
- `fix:`
- `refactor:`
- `docs:`
- `chore:`
- `test:`

## Allowed and Disallowed Actions

### Allowed

- `git status --porcelain=v1 [--branch]`
- `git log`
- `git diff --stat`, followed by selected-file diffs when needed
- local editing, testing, formatting, building, and review steps
- using the wrapper script for write-side GitHub actions

### Disallowed for write-side GitHub workflow

- raw `git push`
- raw `gh pr create`
- raw `gh repo create`
- manually changing remotes as a workaround
- GitHub API write operations used to bypass the wrapper

## Pre-Flight Checklist

Before invoking the wrapper:

1. Confirm whether this is the first commit (`init`), a new PR (`change`), or an update to an existing PR branch (`update`)
2. If this is a new repository, initialize a local Git repository first. The current wrapper aborts immediately unless `.git/` already exists, so the normal preparation step is `git init -b main` (or equivalent) before calling `bash /Users/miqui/development/scripts/git-workflow.sh init ...`.
3. If this is a new repository, verify the local directory name is also a valid GitHub repository name. Avoid characters that GitHub rejects or that may be normalized differently than the local directory name. In particular, do not start a new wrapper-managed repo from a directory containing `+`; rename it to a GitHub-safe slug such as lowercase letters, digits, and hyphens first.
4. Verify branch and modified files with `git status --porcelain=v1 --branch`
5. Ensure generated artifacts and dependency files are up to date
6. For greenfield demos, visualizations, or documentation-heavy repos, decide before publish whether deterministic generated assets should be committed so the repository is immediately reviewable on GitHub. If the user expects to "look at the code" and see the current corpus/config/example output without running a generator first, commit the generated artifact and align the app path, generator output path, and `.gitignore` accordingly (for example, track `data/...` instead of ignoring `public/data/...`).
7. Run relevant verification such as build, tests, or lint checks
8. Ensure every intended new file is explicitly staged before invoking the wrapper when there are already staged changes. The wrapper only auto-runs `git add -A` when nothing is staged; otherwise untracked files like a new `.gitignore` can be silently omitted from the commit.
9. If you need to publish only a reviewed subset (for example docs/design artifacts) while keeping in-progress implementation work local, stage an explicit allowlist and verify both `git diff --cached --stat` and `git diff --stat` before invoking the wrapper. The wrapper's later `Warning: <N> uncommitted changes` is acceptable in this deliberate split-publication flow; after the PR is created, immediately verify that the intended local-only files are still unstaged.
10. In phased implementation work where the user wants a GitHub PR at each checkpoint, publish each checkpoint before starting the next one or explicitly stage only the checkpoint-scoped files. If you let multiple checkpoints accumulate in the working tree, `bash /Users/miqui/development/scripts/git-workflow.sh change ...` will produce a cumulative PR rather than a step-scoped PR.
11. **Stabilize asynchronous work before publishing.** If subagents, generators, formatters, or background processes were involved, do not assume their last report is the final filesystem state. Immediately before staging and invoking the wrapper, run `git status --porcelain=v1 --branch`, inspect both `git diff --cached --stat` and `git diff --stat`, then inspect only the selected-file diffs needed to build an explicit staged allowlist. Recheck `git status --porcelain=v1 --branch` after the wrapper completes. If late formatting or generated-file changes appear, publish them as a deliberately scoped follow-up instead of silently mixing them into an unrelated checkpoint.
12. Confirm the commit message follows Conventional Commits
13. If the user also wants repository metadata such as a description or topics, apply that before or alongside publication using the normal GitHub management tooling; the wrapper governs publication flow, not every non-push repository setting.

## Repository Metadata Follow-Up

After an `init` publish, users may immediately ask for a repository description or similar metadata. That can be handled separately from the wrapper, as long as repo creation/push/PR actions still go through `/Users/miqui/development/scripts/git-workflow.sh`.

Typical example:

```bash
gh repo edit <owner>/<repo> --description "FastMCP server exposing SerpAPI Google Flights search over streamable HTTP"
```

Do not treat metadata edits as permission to bypass the wrapper for subsequent pushes or PR creation.

## Error Handling

If the wrapper exits non-zero:

1. show the stderr output verbatim
2. do not retry automatically
3. do not switch to raw `git`, `gh`, or API workarounds
4. ask the user how they want to proceed

Common examples:

- `SSH auth to GitHub failed` -> SSH key or GitHub auth issue
- `Nothing to commit` -> no changed files are staged or detected
- `GitHub repo already exists` -> may be informational depending on wrapper behavior
- `gh` GraphQL or HTTP 5xx errors after the branch was created and pushed -> treat this as a partial-success run. Inspect the current branch, pushed commit, and working tree before retrying. Explicitly stage any intended new files that were omitted, and if the current branch is itself a PR branch, move the next unit of work onto a clean branch from `main` before invoking `change` again.

## Cross-References

- `references/git-workflow-wrapper-gotchas.md` documents wrapper auto-stage edge cases and partial-success PR-creation failures.
- `references/large-pr-body-recovery.md` documents recovery when a pushed branch's generated PR body exceeds GitHub's limit, including the required wrapper `pr` resume command.
- `references/github-safe-repo-names.md` documents a repo-naming pitfall for wrapper-managed publication, especially local directory names containing `+`.
- `references/greenfield-scaffold-publication-checklist.md` documents the recommended first-publish sequence for newly scaffolded local apps, including ignore-file hygiene, verification before publish, and post-publish metadata updates.
- `references/token-efficient-git-inspection.md` defines porcelain-status and summary-first-diff guidance when Git output enters an agent context.
- `references/pr-pipeline-trigger-triage.md` covers diagnosing an open PR with no checks, correcting `pull_request` triggers, and separating dispatch failures from validation failures.
- Use `go-builder` for Go project structure, framework, testing, Docker, and build guidance
- Use `github-pr-workflow` for general PR lifecycle knowledge when environment-specific wrapper constraints are not the main concern
- Use `github-repo-management` for broader repository operations outside this machine-specific policy

## Common Pitfalls

1. Treating this skill as a general Git tutorial.
   It is a local workflow constraint, not a replacement for general Git knowledge.

2. Using raw `git push` or `gh` because the wrapper seems inconvenient.
   The wrapper is mandatory for write-side GitHub actions in this environment.

3. Hiding raw publication steps inside convenience scripts.
   A local helper with flags like `--push` is still subject to this workflow. If it performs `git push`, `gh pr create`, or other GitHub write-side actions directly, it is non-compliant and should be changed to hand off to `/Users/miqui/development/scripts/git-workflow.sh` instead of bypassing it.

4. Forgetting to decide whether generated artifacts belong in the repository.
   Some repos are not truly reviewable from GitHub alone unless a generated artifact is committed. When the deliverable is a demo corpus, derived catalog, static dataset, or other deterministic output the user expects to inspect in-repo, treat "should this generated file be tracked?" as an explicit publication decision. If it should be tracked, move it to a committed location such as `data/`, update runtime/build paths, and remove the old ignore rule before publishing.

5. Forgetting that the wrapper auto-stages with `git add -A` only when nothing is already staged.
   This can fail in two opposite ways: it can capture more files than intended when the index is empty, or omit new untracked files when some deletions or edits are already staged. Review `git status --porcelain=v1 --branch` carefully and stage an allowlist yourself before invoking the wrapper when the repo contains mixed changes.

6. Publishing a docs/design PR while unrelated implementation work is still in progress.
   In that split-publication case, verify the staged set with `git diff --cached --stat`, verify the unstaged remainder with `git diff --stat`, then invoke the wrapper. The wrapper may still print `Warning: <N> uncommitted changes` when opening the PR; treat that as informational if you intentionally staged only the reviewable subset, but confirm afterward that the remaining local-only files are still uncommitted.

7. Probing the wrapper with `--help` and treating the resulting error as a workflow failure.
   The current script accepts `init`, `change`, `update`, and `pr`; it does not implement a help flag.

8. Hiding raw publication steps inside convenience scripts.
   A local helper with flags like `--push` is still subject to this workflow. If it performs `git push`, `gh pr create`, or other GitHub write-side actions directly, it is non-compliant and should be changed to hand off to `/Users/miqui/development/scripts/git-workflow.sh` instead of bypassing it.

8. Retrying with workarounds when the wrapper fails.
   If the script fails, stop and report the problem.

9. Creating new repositories outside `/Users/miqui/development/`.
   New local projects in this environment belong there unless the user explicitly says otherwise.

10. Assuming `change` only pushes commits.
   The current wrapper also creates a branch and opens a PR automatically.

11. Using a local repository directory name that contains `+` during `init`.
   The wrapper may create the GitHub repo using a normalized slug (for example replacing `+` with `-`) but still set `origin` using the raw local directory name, which leaves the repo in a partial-success state with an invalid remote URL.

## Verification Checklist

- [ ] The task actually involves write-side GitHub workflow on this machine
- [ ] The repository lives under `/Users/miqui/development/` when creating a new local project
- [ ] `init`, `change`, `update`, or `pr` was chosen correctly
- [ ] The wrapper script path is `/Users/miqui/development/scripts/git-workflow.sh`
- [ ] No raw `git push`, `gh pr create`, `gh repo create`, or API workaround was used
- [ ] If the wrapper failed, the failure was surfaced instead of bypassed
