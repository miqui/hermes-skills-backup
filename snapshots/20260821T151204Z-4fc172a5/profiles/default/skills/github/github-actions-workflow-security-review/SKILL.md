---
name: github-actions-workflow-security-review
description: "Review GitHub Actions workflow diffs for privilege-escalation, fork-safety, and token-scope issues (pull_request_target misuse, over-broad permissions, untrusted code running with write-scoped secrets)."
version: 1.1.0
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
  minimum extra scope for their target resource (`pull-requests: write` for a
  PR-only commenter; `issues: write` for an ordinary-issue writer), not the
  whole workflow.
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
- Verify error handling surfaces enough detail to debug CI failures. Do not
  collapse an `HTTPError` to its numeric status alone.

#### 403 triage for trusted PR writers

When a GitHub API write returns `403`, do not immediately widen permissions or
switch tokens. Establish the failing boundary first:

1. Inspect the job's **effective** `GITHUB_TOKEN Permissions` in the runner
   setup log; YAML declares a request, while that log proves the issued scope.
2. Confirm the endpoint's current documented permission sets. For example,
   issue comments on pull requests use the Issues API and accept `issues: write`
   or `pull-requests: write`.
3. Determine whether read calls to the same resource succeeded before the
   write failed. A successful GET plus a failing POST narrows the issue to the
   write authorization or GitHub-side policy/rate-limit path.
4. Preserve only a safe diagnostic field from the error response: parse JSON,
   extract a string `message`, normalize whitespace, and bound its length.
   Never log authorization headers, request bodies, arbitrary error payloads,
   or response headers.
5. Add a regression test with a synthetic `HTTPError` proving the safe message
   reaches the raised error. This is diagnostic instrumentation, not permission
   escalation.

Only after the API's specific message is visible should an agent recommend a
repository/org policy change or a different minimal scope. Do not retry using a
personal token, direct API workaround, or a writer that executes PR-head code.

#### PR comment scope mismatch in Actions

For a writer that targets **pull requests only**, do not assume `issues: write`
is sufficient merely because the REST issue-comments endpoint documents it as
an accepted permission. If the safe diagnostic is `403: Resource not accessible
by integration` and the runner's effective permissions show only `Issues:
write`, treat this as a PR-resource scope mismatch in the `GITHUB_TOKEN`
integration path.

- Replace `issues: write` with `pull-requests: write`; do **not** grant both
  unless the same writer also operates on ordinary issues.
- Preserve `contents: read` and every trusted-writer guard. This is a
  resource-specific least-privilege correction, not a reason to change the
  repository's default Actions policy or introduce a PAT.
- A `pull_request_target` writer runs the workflow and package from the base
  revision. Its original PR cannot prove a changed base workflow configuration.
  Merge the isolated scope fix, then invoke `workflow_dispatch` from the
  default branch with the exact current base SHA and intended PR head SHA.
  Confirm the runner reports `Pull requests: write` and that the comment is
  created or updated.

See `references/trusted-pr-comment-writers.md` for the safe split and live
verification procedure.

#### Non-permission causes of the same 403

Even after confirming the correct scope name (`issues: write` and
`pull-requests: write` are both documented as accepted for
`POST /repos/{owner}/{repo}/issues/{issue_number}/comments` — it's an OR, not
an AND), a 403 can persist for reasons that have nothing to do with the scope
name:
- **Cross-repo/target mismatch**: GITHUB_TOKEN is scoped only to the repo the
  job runs in. If the API call's `{owner}/{repo}` path doesn't resolve to
  `github.repository` (hardcoded upstream repo, template/mirror repo,
  submodule), the write 403s regardless of permissions. Diff the request URL
  against `${{ github.repository }}` before touching the permissions block.
- **Reusable workflow (`workflow_call`) inheritance gap**: permissions do not
  auto-escalate through call chains. If the comment-posting job lives inside a
  called workflow, the *caller* workflow must also declare the same
  `permissions:` at its top level, or the callee is silently capped.
- **Org/enterprise policy cap**: an org can restrict GITHUB_TOKEN below what a
  job's own `permissions:` block requests. The runner's printed
  `Permissions:` log line is not authoritative proof the org hasn't already
  capped the effective token — if request/runner-log permissions look correct
  and the 403 still happens, this is the next thing to suspect, not a signal
  to add more scopes.

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
- A green `workflow_dispatch` run against a permission fix does NOT prove the
  fix works if the run's early-exit branch (e.g. "no changed manifests, no
  comment needed") triggers before the code ever reaches the write call. Check
  the run log for the actual API request/response, not just job success —
  re-dispatch with inputs (PR number, base SHA, head SHA) known to produce a
  non-empty diff, ideally the same PR that originally reproduced the 403.
