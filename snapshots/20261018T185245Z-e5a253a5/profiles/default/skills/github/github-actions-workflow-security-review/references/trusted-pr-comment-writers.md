# Trusted PR Comment Writers

Use this pattern when CI needs to publish a manifest-derived comment, label, or other PR metadata while ordinary validation executes code from the PR head.

## Safe split

1. Keep the validation workflow on `pull_request` with read-only permissions. It may checkout, install, and test the PR head.
2. Put the writer in a separate `pull_request_target` workflow with only the
   write scope for its **target resource**: use `pull-requests: write` for a
   writer that comments on or labels pull requests; use `issues: write` only
   when it operates on ordinary issues. Do not grant both by default.
3. Gate the writer to same-repository PRs:

   ```yaml
   if: github.event.pull_request.head.repo.full_name == github.repository
   ```

4. Checkout the exact base SHA, not the PR head. Install/run only this trusted base revision.
5. If the writer needs PR data, fetch it as data only. For a snapshot delta, derive changed manifest paths with `git diff <base> <head>`, validate every derived ID/path, and checkout only the required manifest JSON files from the head SHA. Never checkout, install, or execute the PR package with the writer token.
6. Use a per-PR concurrency group to prevent duplicate/racing comments.

## Verification constraint

A new workflow file cannot be dispatched until it exists on the repository
default branch. Before merge, validate YAML, test the trusted data-processing
path locally, and verify the normal read-only PR checks. After merge, use
`workflow_dispatch` with exact PR/base/head inputs (or wait for the next PR
event) to prove the live API comment path.

For a permission-only fix, the live dispatch is mandatory: a
`pull_request_target` event executes the base workflow, so a PR carrying the
scope change will otherwise exercise the old base permissions. Record both the
runner's effective permission line and the create/update result.

## Token policy

For `403 Resource not accessible by integration`, first capture the runner's
effective permission line and a sanitized GitHub error `message`. If a PR-only
writer has only `Issues: write`, switch it to `pull-requests: write` before
considering repository or organization policy changes. Request an explicit user
decision before changing repository/org-wide Actions permissions. Preserve
disabled PR-approval capability unless it is separately required.
