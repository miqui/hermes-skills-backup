# Manual restore & branch protection runbook

This document covers two related operational procedures: restoring a
snapshot by hand into a target Hermes home, and the GitHub branch
protection rules this repository expects on its default branch.

## Manual snapshot restore

Restores never touch your live `~/.hermes` unless you explicitly say so.
There is no default `--target-hermes-home` — you must name one every time.

1. **Verify the snapshot first.**

   ```bash
   hsb-verify --snapshots-dir snapshots --snapshot-id <id>
   hsb-validate --snapshots-dir snapshots --snapshot-id <id>
   ```

   Do not proceed if either reports `FAILED`.

2. **Dry-run the restore against your intended target.** This prints the
   full plan (which profiles, which destinations, file counts, whether an
   existing directory would be replaced) without writing anything:

   ```bash
   hsb-restore \
     --snapshots-dir snapshots \
     --snapshot-id <id> \
     --target-hermes-home /path/to/target-hermes-home
   ```

3. **Read the plan carefully.** Confirm the target path is the Hermes home
   you actually intend to restore into (e.g. a fresh machine's `~/.hermes`,
   or a scratch directory for inspection) — restoring into the wrong
   Hermes home will replace that home's existing `skills/` and
   `profiles/*/skills/` directories.

4. **Apply.**

   ```bash
   hsb-restore \
     --snapshots-dir snapshots \
     --snapshot-id <id> \
     --target-hermes-home /path/to/target-hermes-home \
     --apply
   ```

   Every file is staged to a temporary directory and hash-verified again
   immediately before anything under the target is touched. Only the exact
   `skills/` and `profiles/<name>/skills/` directories being restored are
   ever removed — no other file under the target Hermes home, and nothing
   outside it, is ever modified or deleted. The tool also refuses
   unsafe/ambiguous targets outright (filesystem root, your home directory,
   well-known system directories, symlinked targets, or paths that are too
   shallow to be a plausible Hermes home).

5. **Spot-check the result** against `RESTORE.md` inside the snapshot
   directory, which documents the exact commands for that snapshot's id.

## GitHub branch protection

This repository's CI (`.github/workflows/validate-approved-pr.yml`) runs its
tests and changed-snapshot validation for every pull-request lifecycle update
and checks out the exact PR head SHA. For snapshot PRs from branches in this
repository, it also posts one concise, marker-owned delta comment that lists
only new, modified, and removed skill roots; full snapshots remain intact for
standalone restore. Fork PRs receive read-only checks only, avoiding unsafe
write credentials for untrusted code. The default branch should be configured
in GitHub's repository settings with rules along these lines:

1. **Require a pull request before merging.** Direct pushes to the default
   branch are disabled; all changes land through a PR.

2. **Require at least one approving review.** Branch protection makes human
   approval mandatory rather than advisory; CI executes on every PR update so
   reviewers can see validation and the generated delta before approval.

3. **Dismiss stale approvals when new commits are pushed.** Enable "Dismiss
   stale pull request approvals when new commits are pushed" so that an
   approval only ever certifies the exact diff it was given — this is the
   counterpart to the workflow checking out `github.event.pull_request.head.sha`
   rather than a moving branch ref.

4. **Require the status checks from this workflow to pass**, using their exact
   job names (`test`, `detect-changed-snapshots`, and, when a snapshot changes,
   `validate-changed-snapshots`) as they appear once the workflow has run at
   least once on a PR against this branch. Do not require a check by workflow
   file name — GitHub matches status checks by job name.

5. **Do not allow bypassing the above** — disable "Allow specified actors to
   bypass required pull requests" (or, on rulesets, leave bypass lists
   empty) for admins and any other role, so the approval + status-check
   requirement is unconditional.

6. **Restrict who can dismiss reviews / push force-pushes** to the branch,
   and keep "Require branches to be up to date before merging" enabled if
   your merge queue depends on it.

None of this can be configured from within the repository itself (it's a
GitHub repository setting, not a file) — apply it under **Settings → Branches
→ Branch protection rules** (or **Rules → Rulesets** on repos using the newer
rulesets UI) for the default branch.
