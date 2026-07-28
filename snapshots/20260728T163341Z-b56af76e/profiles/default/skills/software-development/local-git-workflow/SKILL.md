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

### Corpus Skill Snapshot PRs

When a new Hermes skill is successfully added to the installed corpus, create a fresh all-profile snapshot and open a dedicated PR in `/Users/miqui/development/hermes-skills-backup` immediately afterward. This is a review checkpoint for the corpus state, not permission to alter the installed skill after capture.

#### Resetting a merged checkpoint workspace safely

Do not infer the prior branch's state from a local checkout or from `gh pr list --state open` alone. A merged PR normally leaves both its local and remote branch behind, while the open-PR list is empty.

1. Check the branch's complete PR history: `gh pr list --repo miqui/hermes-skills-backup --head <branch> --state all --json number,state,url,mergedAt`.
2. If the checkpoint PR is merged and the worktree is clean, refresh the canonical base:
   ```bash
   git fetch origin
   git checkout main
   git merge --ff-only origin/main
   git status --porcelain=v1 --branch
   ```
3. Start the next snapshot checkpoint from that updated `main` worktree. Do not append it to the merged branch, and do not reset or delete a branch until its merged state is verified.

Use this sequence:

1. Refresh the backup workspace from `origin/main`; do not build a new snapshot on a branch whose earlier PR is already merged.
2. Capture the current all-profile corpus with `hsb-snapshot`; run its normal secret scan first. If strict capture aborts, inspect only the reported path/category/line evidence—never print matched values. Before using the repository's documented `--no-secrets-check` exception, compare the current finding pairs (`relative path`, `category`) with the latest merged baseline snapshot using a value-safe scanner. Use the exception only when there are **zero new finding pairs** and the existing findings are confirmed documentation/example placeholders rather than runtime secret stores or real credentials.
3. After any documented exception, keep the validation scan enabled: run both `hsb-verify --snapshot-id <id>` and `hsb-validate --snapshot-id <id>`. Treat validation as successful only when it reports zero errors; documented placeholder findings may remain as warnings. Then run the backup project's regression suite.
4. Explicitly stage only `snapshots/<id>/`; inspect the staged and unstaged summaries so a snapshot PR cannot accidentally carry unrelated changes.
5. Publish using `bash /Users/miqui/development/scripts/git-workflow.sh change "snapshot: ..."`, which creates a new branch and PR. Do not reuse a merged PR branch.
6. Verify the remote branch SHA, PR URL, clean worktree, and the separate Actions jobs for tests, changed-snapshot detection, changed-snapshot validation, and manifest-delta commenting.

### Delta-comment authorization and safety

A snapshot PR can have passing tests and changed-snapshot validation while its optional manifest-delta comment job fails. Treat those as separate signals; do not describe a triggered workflow as fully passing until each required job has completed.

If a same-repository `pull_request` job gets HTTP 403 while posting an issue/PR comment despite declaring job-scoped `issues: write` (or `pull-requests: write`):

1. Inspect the repository Actions workflow-permissions policy read-only. An organization or repository policy may cap `GITHUB_TOKEN` at read-only even when the YAML requests a write scope.
2. Do not retry comment publication using a personal token, raw API workaround, or a `pull_request_target` workflow that checks out or runs the PR head.
3. Do not automatically change repository-wide Actions token policy. Explain the exact required setting and obtain explicit user approval before any GitHub-side settings change.
4. Keep validation jobs read-only. A write-scoped comment job must not install or execute PR-controlled package code; calculate the delta in a read-only job and hand off only validated data to a trusted comment-publishing path.
5. If comments are intentionally best-effort, mark only that job `continue-on-error`; do not hide failure of snapshot tests or validation.

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

### Auditing whether a snapshot PR can be narrowed to changed skills only

When asked to review/audit (read-only) whether a corpus-snapshot PR in a
`hermes-skills-backup`-style repo can be narrowed down to "only new or
modified skills," do not assume this is possible just because most of the
diff is additions. Follow this sequence:

1. Confirm PR state first: `gh pr list --state open`; if empty, `git fetch
   origin` and re-check — a PR merged moments earlier can still look "open"
   from stale local refs.
2. Get the real changed-path set with `git diff --stat <base>..<head>` and
   `git diff --diff-filter=A/M/D --name-only`. A snapshot PR that is 100%
   additions under `snapshots/<id>/**` and touches zero files under `src/`,
   `tests/`, `.github/`, `docs/`, `pyproject.toml` means the pipeline code
   itself is untouched — the "narrowing" question is entirely about snapshot
   *content*, not pipeline behavior.
3. Find the actual delta by diffing the new snapshot directory against the
   immediately prior committed snapshot directory (not against `main`'s
   pipeline code): `diff -rq snapshots/<prev-id>/profiles
   snapshots/<new-id>/profiles`. This reveals the true handful of
   modified/new SKILL.md files versus the thousands of byte-identical
   re-copied files.
4. Check the README/tool contract before recommending a change: if the tool
   documents each snapshot as a complete, standalone, hash-verified
   directory tree (`hsb-verify` enforces "no missing or extra files") and
   restore replaces a whole profile's skills directory from one snapshot,
   then a per-PR full-corpus snapshot is a *design invariant*, not a bug —
   hand-pruning the PR to only the delta files would break `hsb-verify`/
   `hsb-validate` and make the snapshot non-restorable standalone.
5. Also check whether CI has already solved the real cost concern: this repo's
   `.github/workflows/validate-approved-pr.yml` already diffs
   `snapshots/*/MANIFEST.json` between PR base/head SHAs and validates only
   the snapshot(s) actually changed, deferring full-corpus audit to
   `schedule`/`workflow_dispatch`. If that job exists, PR-time review/CI cost
   is already scoped — don't recommend re-solving a problem CI already
   handles.
6. Report the finding as: exact non-snapshot paths touched (should be zero
   for a pure snapshot PR), exact modified/new skill paths found in step 3,
   and whether narrowing requires a pipeline feature change (e.g. delta/dedup
   snapshots) rather than a PR-level edit. Do not modify files or push
   anything during a read-only audit — this whole procedure is inspection
   only (`git diff`, `diff -rq`, `read_file`), never `git add`/commit/wrapper
   calls.

## Cross-References

- `references/git-workflow-wrapper-gotchas.md` documents wrapper auto-stage edge cases and partial-success PR-creation failures.
- `references/large-pr-body-recovery.md` documents recovery when a pushed branch's generated PR body exceeds GitHub's limit, including the required wrapper `pr` resume command.
- `references/github-safe-repo-names.md` documents a repo-naming pitfall for wrapper-managed publication, especially local directory names containing `+`.
- `references/greenfield-scaffold-publication-checklist.md` documents the recommended first-publish sequence for newly scaffolded local apps, including ignore-file hygiene, verification before publish, and post-publish metadata updates.
- `references/token-efficient-git-inspection.md` defines porcelain-status and summary-first-diff guidance when Git output enters an agent context.
- `references/pr-pipeline-trigger-triage.md` covers diagnosing an open PR with no checks, correcting `pull_request` triggers, and separating dispatch failures from validation failures.
- `references/pr-delta-comment-design.md` covers designing a concise, idempotent CI-posted PR-delta comment on top of a snapshot pipeline: deriving the delta from sortable snapshot IDs/manifests, the fork-PR read-only-token trap, the GET→PATCH/POST idempotent upsert pattern, and preserving the full-standalone-snapshot invariant.
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
