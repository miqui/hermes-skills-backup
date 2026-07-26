---
name: github-actions-workflow-security-review
description: "Review GitHub Actions workflow diffs for privilege-escalation, fork-safety, and token-scope issues (pull_request_target misuse, over-broad permissions, untrusted code running with write-scoped secrets)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Actions, CI, Security, Code-Review]
    related_skills: [github-code-review, github-pr-workflow]
---

# GitHub Actions Workflow Security Review

Use this whenever a diff touches `.github/workflows/*.yml`, or when asked to
audit/harden CI for a repo. Workflow files are code that runs with real
credentials against PR-controlled input, so review them like an authz
boundary, not like ordinary config.

## The core threat model

A workflow is dangerous when **all three** of these are true in the same job:
1. It checks out or otherwise executes code from a pull request (untrusted input).
2. It holds a token/secret with write scope (`issues: write`, `contents: write`,
   `pull-requests: write`, deploy keys, npm/PyPI tokens, etc.).
3. Nothing gates (1) away from (2) for fork-originated PRs.

## Checklist

### 1. Trigger + checkout pattern
- **Never `pull_request_target` when the job also checks out/builds/runs the PR
  head ref.** `pull_request_target` runs with the base repo's secrets and
  permissions regardless of who opened the PR — combining it with PR-branch
  code execution is the textbook escalation (this is how many high-profile
  Actions CVEs happened). If a job needs both write access *and* to run PR
  code, it must gate on same-repo origin instead:
  `github.event.pull_request.head.repo.full_name == github.repository`.
- `pull_request` (not `_target`) + a job-scoped `permissions:` override is the
  correct default for "safe checks on every PR, elevated action only for
  trusted PRs."

### 2. Permission scoping
- Look for `permissions: write-all` or a missing `permissions:` block at the
  workflow level (defaults can be write-all on older repos/orgs) — permissions
  should be `contents: read` at the top, with specific jobs opting into the
  minimum extra scope they need (`issues: write` only on the job that comments,
  not the whole workflow).
- Confirm the elevated-scope job doesn't ALSO run untrusted install/build steps.
  Even with a correct fork-safety `if:` gate, a same-repo contributor's branch
  can still smuggle malicious code into `pip install -e .`, `npm ci`, a
  Makefile, postinstall hooks, etc. If that install step runs in the same job
  that already holds the write token, the token is exposed during install —
  before the "safe" action ever executes. Prefer: one read-only job that does
  the checkout/build/compute and uploads an artifact or job output, and a
  second, separate job with the elevated permission that only consumes that
  output and calls the API. This is a WARNING even when the top-level fork gate
  is correct — don't let a correct `if:` condition hide this residual risk.

### 3. Idempotency / API usage details
- Any "create-or-update a single comment/check" pattern needs to search
  existing items first. Verify pagination — a bare `?per_page=100` with no
  loop over subsequent pages will silently start duplicating past that count.
- Verify error handling surfaces enough detail to debug CI failures (don't
  swallow `HTTPError` response bodies).

### 4. Supply-chain hygiene
- `uses: owner/action@<tag>` should be pinned to a full commit SHA with a
  version comment (`@abcdef... # v4.2.2`), not a mutable tag/branch — tags can
  be moved after the fact.
- `persist-credentials: false` on `actions/checkout` for jobs that don't need
  git push access, to avoid leaving a token lying around in the workspace.

### 5. Resilience / noise
- Non-required, best-effort jobs (audits, optional delta comments) should use
  `continue-on-error: true` so transient API failures don't show as blocking
  red X's on unrelated PRs.
- Consider a `concurrency:` group keyed on the PR number for any job that
  posts/updates PR comments, so rapid pushes can't race each other into
  duplicate comments.

## Review output

Fold these findings into the same Critical / Warning / Suggestion format used
for general code review (see `github-code-review` skill) — don't produce a
separate report structure. Fork-safety violations (checklist item 1) are
Critical. Token-exposure-during-install and missing pagination are typically
Warning. Pinning/concurrency/continue-on-error are Suggestion-level polish.

## Pitfall log
- A workflow can have a textbook-correct fork-safety `if:` gate on the
  comment-posting job and still be exposing the write token, because the
  *same job* installs the package from the PR branch before posting the
  comment. Always check job-internal ordering, not just the job-level `if:`.
