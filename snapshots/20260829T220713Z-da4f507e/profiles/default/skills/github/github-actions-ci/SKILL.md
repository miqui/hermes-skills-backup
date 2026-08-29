---
name: github-actions-ci
description: "Use when adding or changing GitHub Actions CI workflows."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [GitHub, Actions, CI, Automation, Security]
    related_skills: [github-actions-workflow-security-review, github-pr-workflow, local-git-workflow]
---

# GitHub Actions CI

Use this skill when adding, replacing, or materially changing a GitHub Actions
CI workflow. It covers the delivery path from repository discovery through a
verified hosted run. Use `github-actions-workflow-security-review` alongside it
when the workflow has write permissions, comments on pull requests, uploads
security results, deploys, or consumes credentials.

## Outcomes

A completed CI change has all of the following:

1. A workflow scoped to the intended events and repository paths.
2. Explicit least-privilege permissions and safe handling of PR-controlled
   code.
3. Immutable pins for third-party actions.
4. A focused diff with no unrelated configuration churn.
5. A real GitHub Actions execution from the proposed commit, with the intended
   job and steps completed.

A locally valid YAML file is not sufficient evidence that an action or
container can run on GitHub-hosted infrastructure.

## 1. Discover before designing

Before authoring a workflow, inspect the target repository and answer:

- Does `.github/workflows/` already establish names, action pins, runner
  versions, reusable workflows, or permissions conventions?
- Are there repository instructions (`AGENTS.md`, `CLAUDE.md`, CI docs) or a
  required local publication wrapper?
- Which directories and file types contain the actual source to test or scan?
- Is the job a read-only check, a report publisher, or a deployment action?
- Which event needs coverage: pull request, default-branch push, manual run,
  scheduled run, or a trusted release event?

Preserve existing conventions unless they create a security or correctness
problem. Prefer one purpose-built workflow over a broad refactor of unrelated
CI.

## 2. Choose the trigger and authority boundary

Use `pull_request` as the default event for checks that checkout, build, test,
or scan PR content. This event gives fork PRs a safely restricted token.

Do not use `pull_request_target` merely to access secrets or write permission
when the job executes PR-controlled code. That combines attacker-controlled
input with base-repository authority. Split any trusted reporting or deployment
stage into a separately reviewed job or workflow.

Add a default-branch `push` trigger when it provides useful continuous coverage
of merged code. Add `workflow_dispatch` only when a meaningful manual recovery
or diagnostic path is required. Avoid schedule triggers by default; they create
noise and costs unless recurring drift or freshness has a clear owner.

## 3. Build a minimal secure workflow

For an ordinary read-only CI job:

1. Set `permissions: { contents: read }` at workflow level.
2. Check out source with `actions/checkout` pinned to a full commit SHA and set
   `persist-credentials: false` unless the job must publish with Git.
3. Pin every other third-party `uses:` reference to a full immutable commit SHA
   with a nearby version comment. Resolve and verify the SHA against the
   upstream repository before use.
4. Run only the task required by the job. Do not add comments, artifacts,
   security uploads, caches, or credentials without a stated need.
5. Scope tools to their source roots. Exclude generated output, dependency
   caches, and broad repository paths where they do not belong.
6. Keep correctness, test, and policy gates blocking by default. A new scanner
   should surface findings; do not set `continue-on-error` or a scanner
   `soft_fail` switch just to make rollout green.

Quote the `"on"` key when local YAML 1.1 parsers are part of the validation
path. GitHub accepts unquoted `on`, but quoting preserves the key consistently
across common local parsers without changing GitHub behavior.

Use the smallest runner surface that supports the tool. GitHub-hosted runners
are suitable for read-only checks unless the project has an explicit self-hosted
requirement.

## 4. Review the diff before publication

Check each workflow for:

- the correct event and branch filters;
- the intended source directory;
- explicit minimal permissions;
- full-SHA action pins with version comments;
- no PR-head execution with write-scoped secrets;
- no untrusted expression interpolated into an unsafe shell command;
- no credentials or secret-like values in workflow text;
- an exact allowlist of changed files.

Use a YAML parser and `git diff --check` as syntax and whitespace preflight.
Run the repository’s configured secret scanner where available. These are
preflight checks; they do not replace execution on GitHub.

## 5. Publish according to repository policy

If the host or repository mandates a wrapper for branches, commits, pushes, or
pull requests, load `local-git-workflow` and use that wrapper exclusively. Do
not fall back to raw publication commands when the wrapper fails.

Stage only the intended workflow and its directly required files. Before
publication, verify the staged diff and ensure no untracked or unstaged files
remain outside scope. Use a `ci:` commit title for CI-only changes where the
repository follows Conventional Commits.

## 6. Accept only a real hosted run

After opening the pull request:

1. Confirm the remote PR contains only the intended files and targets the right
   base branch.
2. Watch the relevant check to completion using GitHub’s job/check status.
3. Inspect the completed run details. Confirm the expected checkout and primary
   tool steps completed, and that the final conclusion matches the intended
   gate behavior.
4. If the run fails, diagnose the workflow or tool configuration from its
   GitHub log. Do not hide genuine test or policy findings to force success.
5. Report the PR URL, run URL, job conclusion, and any intentionally deferred
   follow-up to the user.

A local container or action test may be helpful, but external image pulls,
credential helpers, and runner differences can make it non-authoritative. A
successful real GitHub run is the acceptance evidence for a GitHub Actions
change.

## Terraform policy scans

When the CI change is an IaC policy scan, pair with `terraform-infrastructure`.
Use the focused pattern in
`references/terraform-policy-scan.md`: scan Terraform source only, preserve
read-only CI, and validate the action through a real PR run. Do not run
Terraform apply or expose cloud provider credentials merely to add static
policy scanning.

## Common pitfalls

1. **Treating YAML validity as CI validation.** A parser cannot prove that the
   action can pull its image, access the workspace, or interpret its inputs on
   a hosted runner.
2. **Using a mutable action tag.** Tags can move. Pin the full commit SHA and
   retain a readable release comment.
3. **Adding writes with a read-only check.** Result uploads and PR comments
   often require broader permissions; keep them out of the baseline workflow
   unless they are a reviewed requirement.
4. **Scanning too much.** Dependency caches, generated files, provider
   binaries, and unrelated directories add noise and can make policy results
   misleading.
5. **Suppressing failures during rollout.** A non-blocking scanner trains teams
   to ignore it. Fix findings or explicitly document approved exceptions.
6. **Publishing through the wrong mechanism.** Wrapper policies apply to CI
   changes just as they do to application code.
7. **Declaring success before the hosted run ends.** The PR check is the final
   evidence, not a queued status or a local simulation.

## Verification checklist

- [ ] Existing workflows and repository instructions were inspected
- [ ] Trigger uses `pull_request` for PR-controlled code
- [ ] Permissions are explicit and minimal
- [ ] All third-party actions are pinned by full SHA with version comments
- [ ] The checked-out token is not persisted unnecessarily
- [ ] Scanner/test scope targets source, not generated or cached content
- [ ] Preflight YAML, diff, and secret checks passed
- [ ] The published PR has only intended changed files
- [ ] The expected GitHub Actions job completed with the intended conclusion
- [ ] The final report includes copyable PR and run links
