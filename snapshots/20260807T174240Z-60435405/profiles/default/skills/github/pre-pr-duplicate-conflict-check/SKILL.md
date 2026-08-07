---
name: pre-pr-duplicate-conflict-check
description: "Read-only reconnaissance to determine whether pending/uncommitted local changes would duplicate, conflict, or remain complementary to work already merged or open as a PR, before creating a new pull request. Strictly read-only: no fetch (non-dry-run), pull, checkout, stage, commit, or push."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [GitHub, Git, PR, Read-Only, Reconnaissance, Merge-Conflict]
    related_skills: [github-pr-workflow, github-code-review, checkpointed-repo-publication]
---

# Pre-PR Duplicate/Conflict Check

Use this when asked to inspect whether uncommitted or pending local work would
duplicate, conflict with, or remain complementary to content already merged
or in flight on GitHub — as a gate BEFORE opening a PR. This is a distinct
task from actually publishing (see `github-pr-workflow` /
`checkpointed-repo-publication` for that). Treat the request as strictly
read-only unless the user explicitly asks you to proceed to publish:
do not `fetch` (non-dry-run), `pull`, `checkout`, `git add`/stage, `commit`,
or `push`.

## Workflow

1. **Snapshot current state without mutating anything.**
   ```bash
   git status
   git branch -a
   git remote -v
   ```

2. **Find the PR tied to the branch/topic in question.**
   ```bash
   gh pr list --state all --search "<branch-name-or-topic>"
   gh pr view <number-or-branch>   # state: OPEN / MERGED / CLOSED, body, summary
   ```

3. **Never trust a local `origin/<branch>` tracking ref — it can be stale.**
   A local remote-tracking ref only updates on `fetch`. Compare it against the
   real remote tip using read-only calls that never mutate local git state:
   ```bash
   git ls-remote origin main HEAD        # actual current SHA on GitHub
   git fetch --dry-run origin main       # reports what's new, applies nothing
   gh api repos/<owner>/<repo>/contents/<path> -q '.content' | base64 -d
   # reads a file's ACTUAL current remote content directly via the GitHub API,
   # the most reliable way to inspect current main when local refs are stale,
   # with zero git state touched at all.
   ```
   If `git ls-remote` disagrees with your local `origin/main`, say so explicitly
   in the report — it usually means other PRs merged since the last fetch, and
   any file-content diff, line-anchor comparison, or page/section count check
   against the stale local ref will be wrong.

4. **Enumerate what the target PR actually touched.**
   ```bash
   gh pr view <number> --json files -q '.files[].path'
   ```
   Diff that file list against the new/uncommitted files:
   - **By name first** — fast, cheap duplicate signal (same path = definite overlap).
   - **By content next** — semantic overlap even without a name collision (e.g.
     two docs pages describing the same concept from different source articles,
     or two commits both adding a changelog entry for the same feature).

5. **Check commit ordering / drift.**
   ```bash
   git rev-list --count HEAD..origin/main
   git rev-list --count origin/main..HEAD
   ```
   This explains diff-context mismatches in files that get appended to on every
   merge (index/catalog files, running changelogs, count/total-lines that bump
   each PR) — a mismatch here is a mechanical-conflict signal, not a content
   problem.

6. **Classify and report.** Use these four verdict buckets, not vague prose:
   - **Duplicate** — same content/topic already merged under a different name.
   - **Conflict** — mechanical; stale line anchors, counts, or context lines in
     shared bookkeeping files (index, changelog, manifest) that will fail to
     apply or merge cleanly against current `main`.
   - **Complementary** — new topic/file, no overlap with anything merged or open.
   - **Content-overlap-without-file-collision** — worth flagging even though git
     itself won't see a conflict: e.g. two pages/functions/docs covering the
     same concept from different sources, which a reviewer would want
     consolidated or cross-linked rather than left as parallel entries.

## Snapshot-Backed Corpora (e.g. hermes-skills-backup style repos)

Some repos don't track individual source files directly — they commit
periodic, complete, hash-verified **snapshots** of an external corpus (e.g.
a `snapshots/<id>/MANIFEST.json` capturing an entire local skills directory
tree). For these, "is this already covered?" isn't a file-path/content diff
against `main` — it's a freshness check against the latest committed
snapshot:

1. Compare the target item's on-disk mtime against the latest snapshot
   commit's timestamp: `stat -f "%Sm" <path>` (macOS) or `stat -c "%y" <path>`
   (Linux) vs. `git log -1 --format=%ci <snapshot-commit-sha>`.
2. Grep the latest snapshot's manifest for the item's identifying path/name
   (e.g. `grep -i "<skill-name>" snapshots/<latest-id>/MANIFEST.json`).
3. If the item's mtime postdates the latest snapshot AND/OR it's absent from
   the manifest, a new snapshot PR is warranted — this is a "complementary"
   verdict, not a duplicate. If it's already present and unchanged, report
   that no new snapshot is needed rather than proceeding to capture one.

This generalizes the duplicate-check principle above to periodic-snapshot
repos where the natural "existing work" unit is a manifest entry, not a
tracked file.

## Pitfalls

- Assuming "0 commits ahead of origin/main" means your branch is caught up —
  check whether your *tracked* `origin/main` itself is stale relative to the
  true remote tip (`ls-remote`/`gh api`), especially in repos with frequent
  merge activity. A stale tracking ref silently produces wrong page counts,
  wrong "already exists" conclusions, and wrong diff context.
- In a snapshot-backed repo, don't rely on `git diff --stat` against `main`
  to answer "is X already captured?" — a full-corpus snapshot commit will
  show thousands of unrelated re-copied files as "changed" even when X truly
  hasn't been snapshotted yet. Use the mtime/manifest-grep check above
  instead, and don't treat GitHub branch-protection documentation
  (`docs/branch-protection.md` or similar) as proof of live repository
  settings — verify with `gh api repos/<owner>/<repo>/branches/<branch>/protection`
  directly, since the doc can describe intended policy that was never
  actually applied in GitHub's settings.
- Treating a PR's file list alone as sufficient — always also check content,
  since new work can duplicate a *topic* without touching the same file path.
- Running any command in this workflow that mutates state (`fetch` without
  `--dry-run`, `pull`, `checkout`, `add`, `commit`, `push`) when the user asked
  for a read-only check — that silently converts a review task into a
  publish/merge action they didn't request.
- Skipping the `gh api .../contents/<path>` read when `git ls-remote` shows
  drift — it's the only way to see exact *current* remote file content
  without any local git state change.

## Related Skills

- `github-pr-workflow` — once the check clears and the user wants to actually
  open the PR, hand off to the normal PR lifecycle.
- `checkpointed-repo-publication` — if only a subset of local changes should
  ship even after this check clears.
- `local-git-workflow` — if the host mandates a publication wrapper for any
  follow-up push/PR action.
