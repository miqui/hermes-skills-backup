# PR Pipeline Did Not Trigger

Use when an open, non-draft PR has no checks or Actions runs.

## Read-only triage

```bash
gh pr checks <pr-number> || true
gh pr view <pr-number> --json state,isDraft,headRefName,baseRefName,statusCheckRollup,url
gh workflow list
gh run list --limit 20
git show origin/main:.github/workflows/<workflow>.yml
```

## Trigger audit

1. Inspect workflow `on:` events before assuming Actions is unavailable.
2. `pull_request_review` fires only after a review submission, not when a PR opens or gets new commits.
3. A guard such as `if: github.event.review.state == 'approved'` skips ordinary PR events.
4. Normal PR validation needs `on: pull_request:`; reserve approval-only guards for intentional post-review gates.
5. Publish the workflow fix with the local wrapper's `update` command on the existing PR branch, then check for both a check and a run.

## Interpret result

- **No run/check:** trigger, filters, draft state, workflow location, or job `if` is wrong.
- **Run starts then fails:** dispatch works. Use `gh run view <run-id> --log-failed`; fix validation separately.
- Historical snapshot repositories may fail all-snapshot validation on pre-existing baseline findings. Do not misreport that as a dispatch failure or silently modify unrelated source skills.
