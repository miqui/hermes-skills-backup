---
name: checkpointed-repo-publication
description: Publish a reviewable subset of repo changes during phased work without accidentally shipping unfinished local changes; especially useful for docs-only or checkpoint-scoped PRs while implementation continues locally.
tags: [git, publication, pull-requests, checkpoint, review, workflow]
---

# Checkpointed Repo Publication

## When to use
Use this skill when:
- The user asks to push only a subset of work (for example docs, ADRs, plans, or one completed checkpoint) while other implementation is still in progress locally.
- You are in a phased design/plan/build workflow and need a clean review artifact before continuing.
- The repo or host has a required publication wrapper or policy that must be respected.

## Goal
Publish exactly the intended review slice, keep unfinished work local, and report clearly what was shipped versus what remains unpublished.

## Workflow
1. **Define the publication slice explicitly**
   - Restate what should be published now.
   - Treat everything else as out of scope until verified otherwise.

2. **Inspect staged vs unstaged state**
   - Check branch and working-tree state with `git status --porcelain=v1 --branch`.
   - Check staged (`git diff --cached --stat`) and unstaged (`git diff --stat`) separately.
   - Never assume the current index already matches the user's intent.

3. **Protect unfinished work**
   - If the user asked for a docs-only or checkpoint-only publish, do not use broad staging.
   - Stage only the intended files, or verify that only the intended files are already staged.
   - Keep unrelated implementation changes unstaged and local.

4. **Respect repo-specific publication workflow**
   - If the repo or user environment requires a wrapper script or house workflow, use it.
   - Do not bypass required automation with raw `git push` or `gh pr create` unless the governing workflow explicitly allows it.

### Complete artifacts: reduce review noise without narrowing the artifact

A reviewable slice is not always a smaller committed artifact. For immutable
backup snapshots, lockfiles, generated catalogs, or other artifacts whose
contract requires a complete standalone tree, do **not** hand-prune the PR to
only changed files. First verify whether integrity, restore, or consumer logic
requires the full artifact. If it does, keep the full artifact and add a
compact, deterministic review summary instead.

For snapshot-style artifacts, derive that summary from structured metadata
(for example, manifests and content hashes), compare with the immediate prior
artifact, and group changed files by their owning unit (such as the nearest
`SKILL.md` directory). Report added, modified, and removed units; include
unscoped files separately rather than silently hiding them. Keep the generated
review text value-safe: paths, categories, and hashes are acceptable; secret
values and copied content are not.

When publishing the summary as a PR comment, use a stable hidden marker and
update the existing marked comment rather than adding duplicates on each
workflow run. For GitHub Actions, run write-side commenting only for
same-repository `pull_request` events with the smallest required permission;
do not use `pull_request_target` merely to comment on fork PRs. Keep fork PRs
read-only validated. See `references/full-artifact-pr-deltas.md` for the
implementation and verification checklist.

### Snapshot validation with legacy scanner findings

A full-corpus snapshot can surface validator findings in pre-existing content
outside the publication slice. Do not edit unrelated installed content just to
silence those findings. Instead:

1. Run a targeted, value-safe scan of the new or changed artifacts first.
2. Run snapshot integrity verification and full validation; record the exact
   error/warning outcome without exposing secret-like values.
3. If a scanner blocks snapshot creation, review every flagged source path and
   determine whether it is a known documentation/example false positive before
   using any scanner-bypass option. Record the reason, scope, and bypass in the
   PR summary.
4. A snapshot with zero validation errors and pre-existing warnings may be
   published when project policy permits it. Do not describe it as a clean scan;
   report the warning count and that it predates the publication slice.
5. Keep the snapshot complete. The manifest-derived delta is the review aid;
   it is not a reason to remove legacy files from the artifact.

This preserves corpus integrity while keeping new changes accountable.

5. **Publish the slice**
   - Use a commit message that matches the review slice (for example `docs: ...` for docs-only publication).
   - Expect wrapper workflows to create a new branch and PR; verify the exact outputs rather than assuming them.

6. **Verify the post-publish state**
   - Re-check `git status --porcelain=v1 --branch` and the last commit.
   - Confirm which files were published and which files remain local-only.
   - Tell the user the branch, commit, PR URL, and remaining unpublished files.

7. **Pause cleanly if the user is reviewing**
   - If the user wants to review the published slice before resuming implementation, stop the build lane and preserve the exact local checkpoint.
   - On resume, re-inspect repo state before continuing.

## Output checklist
Always report:
- What was published
- Branch / commit / PR details
- What remains local-only
- Whether implementation is paused pending review

## Pitfalls
- Accidentally sweeping unfinished work into a review PR with broad staging
- Assuming staged content is safe without checking the cached diff
- Forgetting that temporary verification files can enter typecheck or publication scope if left in the repo
- Reporting success without verifying the wrapper's actual branch/PR outputs

## Deferred-to-wrapper: preparing a staged-but-uncommitted isolated worktree

Some checkpointed-publication tasks explicitly want the work brought to a
**staged, verified, uncommitted** state in an isolated worktree, then stopped
— no commit, no branch beyond what staging needs, no PR, no wrapper call —
because a separate mandatory process (a different agent, a CI job, a human)
does the actual publish later. Treat "prepare for publication" and "publish"
as two different terminal states; when the task says "do not commit/push/PR/
run the wrapper," honor that literally even though the rest of this skill's
instinct is to get to a merged/opened PR.

1. **Hard stop-if-exists on any named target path.** If the caller gives an
   exact target worktree/output path, its prior existence is a stop-and-report
   condition — never `rm -rf` and reuse it, even to "clean up."
2. **Pin the base precisely.** `git worktree add --detach <target>
   <exact-base-sha-or-ref>` (e.g. a specific `origin/main` SHA named by the
   task, not "current HEAD"). Verify the new worktree's HEAD SHA matches
   before doing anything else in it.
3. **Copy only the approved subtree**, excluding build/dependency artifacts
   (`node_modules`, `dist`, `.serverless`, `coverage`, etc.) via `rsync -av
   --exclude ...`, preserving lockfiles. If the copied directory already has
   its own `.gitignore` covering those same paths, later `git add <dir>`
   will naturally exclude them — no need to hand-delete post-copy artifacts.
4. **Run only the named local verification commands** (install/typecheck/
   build/test) inside the target worktree, never the source checkout.
   Explicitly skip anything that authenticates, deploys, or publishes (e.g.
   `serverless login/deploy/package/print`, `npm publish`) even if it exists
   as a package script — only run what the task names as safe/local.
5. **Run the mandated secret scanner** on the copied subtree before staging
   (see `secret-scan-triage` skill for classification method); report only
   the aggregate pass/fail line and finding counts, never matched values.
6. **Stage only the approved path** with an explicit `git add <subdir>` (not
   `git add -A`), then report `git status --porcelain=v1 --branch`, `git diff
   --cached --stat`, and the exact staged path list as evidence the staging
   is scoped correctly.
7. **Stop there.** Do not commit, do not create the final PR branch, do not
   push, do not invoke a publish wrapper — say explicitly in the report that
   the worktree is left staged-but-uncommitted on purpose for a downstream
   step to finish.
8. **Re-confirm the source checkout is untouched**: same branch name, same
   `git status --porcelain=v1 --branch` output as before starting, and
   `git worktree list` showing the new worktree as a distinct entry pointing
   at the pinned base SHA.

## Verification
- The intended subset is the only content staged or published.
- Unfinished work remains local if the user did not ask to publish it.
- The reported branch/commit/PR metadata matches the actual post-publish repo state.

## Notes
- This skill overlaps with GitHub publication and local git workflow skills; use it as the slice-control layer when the main challenge is partial publication during checkpointed work.