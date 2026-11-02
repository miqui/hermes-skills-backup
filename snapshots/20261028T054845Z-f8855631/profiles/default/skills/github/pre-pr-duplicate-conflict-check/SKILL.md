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

The same read-only discipline applies to a related but distinct ask:
**independently verifying an already-open/already-reported PR** (e.g. "verify
PR #N was opened correctly, without making any writes"). See
"Independently Verifying an Already-Open PR" below for that recipe —
it reuses this skill's read-only tool set (`gh`, `git ls-remote`,
`gh api .../contents`) but checks a different set of claims (PR
metadata/mergeability, changed-file list, head-SHA-vs-remote, declared
content hashes, and that any local checkout used to produce the PR was
left in its pre-existing state).

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

## Verifying External Technical Claims in Reviewed Content

When the diff/review under this workflow includes provider/vendor technical
claims (e.g. a devops/infra skill's reference doc asserting "Backups require
an unencrypted filesystem" or "the firewall defaults to deny-inbound"), don't
accept the claim on the strength of citing an official-looking URL alone:

1. Fetch the live cited page (`browser_navigate`) and grep the saved snapshot
   text for the exact wording the reviewed content claims — matching precise
   phrasing against the live page is much stronger evidence than "the topic
   seems covered."
2. Treat a reviewed doc's own explicit caution ("this is an unresolved
   documentation inconsistency, verify at execution time") as a passing
   signal, not a defect — confirm the cited pages still say what it claims,
   then credit the hedge.
3. Fail closed if the cited page no longer says what's claimed, has moved, or
   can't be verified — don't wave a PR through because the claim "sounds
   plausible."

This generalizes the existing duplicate/conflict verdict discipline: a
technical claim that can't be verified against its cited source is itself a
material issue worth flagging in the pass/fail decision, separate from the
duplicate/conflict/complementary classification.

## Independently Verifying an Already-Open PR

Use this when asked to verify (not create) a PR — confirm its metadata is
accurate, its content matches what's claimed, and any local checkout used to
produce it was left untouched. Fully read-only: no fetch/pull/checkout/stage/
commit/push, and no writes anywhere in the repo or checkout.

1. **Pull PR metadata in one shot:**
   ```bash
   gh pr view <N> --repo <owner>/<repo> --json \
     url,state,baseRefName,headRefName,headRefOid,mergeable,mergeStateStatus,statusCheckRollup,files,title,body
   ```
   Cross-check `.files[]` (path/additions/deletions/changeType) against
   whatever changed-file list the PR body or report claims — a body's
   free-text file table (e.g. from a `git diff --stat`-style summary) should
   match the structured `.files` array file-for-file.

2. **Confirm head SHA against the real remote, two independent ways:**
   ```bash
   git ls-remote origin <head-branch-name>          # via configured origin (works even over SSH)
   gh api repos/<owner>/<repo>/git/refs/heads/<head-branch-name> --jq '.object.sha'
   ```
   Both must equal `headRefOid` from step 1. Don't reach for
   `git ls-remote https://github.com/<owner>/<repo>.git` as a first choice —
   if the repo's `origin` remote is SSH-based (`git@github.com:...`),
   unauthenticated HTTPS ls-remote fails with "Invalid username or token"
   even though the repo and PR are perfectly fine. Use `git ls-remote origin`
   (respects whatever auth the remote is already configured with) or the
   `gh api .../git/refs/heads/<branch>` call instead — this is a command-choice
   fix, not evidence of anything wrong with the PR.

3. **Confirm wiki/repo artifacts are actually present at the head commit:**
   ```bash
   gh api repos/<owner>/<repo>/git/trees/<headRefOid>?recursive=1 \
     --jq '.tree[] | select(.path=="<path1>" or .path=="<path2>") | .path'
   ```

4. **Recompute a declared content hash (e.g. SHA-256 of a file body after
   frontmatter) directly from the PR's remote content — don't trust the
   number in the PR body/log without recomputing it:**
   ```bash
   gh api "repos/<owner>/<repo>/contents/<path>?ref=<headRefOid>" --jq '.content' \
     > /tmp/file_b64.txt
   # macOS base64 requires -D (uppercase) to decode, and -i/-o flags, not stdin/stdout redirection:
   base64 -D -i /tmp/file_b64.txt -o /tmp/file_decoded.md
   # Linux base64 uses lowercase -d and accepts stdin/stdout redirection instead.

   # Split at the SECOND '---' delimiter (end of YAML frontmatter), hash only the body:
   awk 'BEGIN{c=0} /^---$/{c++; if(c==2){found=1; next}} found{print}' \
     /tmp/file_decoded.md > /tmp/file_body.md
   shasum -a 256 /tmp/file_body.md     # macOS/BSD
   # sha256sum /tmp/file_body.md       # Linux
   ```
   Compare the resulting hash byte-for-byte against the declared value in the
   file's frontmatter / the PR body / the log entry. This is the strongest
   evidence in the whole verification — a matching recomputed hash proves the
   remote content is exactly what's claimed, independent of anything the PR
   author asserts.
   Note: plain `curl -s https://raw.githubusercontent.com/<owner>/<repo>/<sha>/<path>`
   can silently fail (empty file, non-zero exit) in sandboxed/approval-gated
   terminals depending on network egress rules — if that happens, fall back
   to the `gh api .../contents` + `base64 -D` route above rather than
   concluding the file doesn't exist.

5. **Confirm an original local checkout was left untouched** (when the PR was
   produced by an agent working in an isolated worktree/temp clone while a
   primary checkout had pre-existing uncommitted work):
   ```bash
   cd <original-checkout-path>
   git status --short          # expect exactly the pre-existing dirty/untracked files, nothing more
   git branch --show-current   # expect the pre-existing branch, unchanged
   git stash list              # expect the same pre-existing stash entries, none added/removed
   ```
   Report the exact dirty-file list and stash description verbatim so a
   mismatch (new dirty file, changed branch, extra/missing stash) is obvious.

6. **Report using the same evidence-first structure as a duplicate/conflict
   check** — lead with concrete command output (SHAs, file lists, hash
   match/mismatch, git status lines), not prose summaries. Call out any
   discrepancy explicitly; if everything matches, say so explicitly too
   rather than only reporting absence of problems.

## Related Skills

- `github-pr-workflow` — once the check clears and the user wants to actually
  open the PR, hand off to the normal PR lifecycle.
- `checkpointed-repo-publication` — if only a subset of local changes should
  ship even after this check clears.
- `local-git-workflow` — if the host mandates a publication wrapper for any
  follow-up push/PR action.
