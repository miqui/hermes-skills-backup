---
name: corpus-change-governance
description: "Use before mutating any Hermes skill corpus file."
version: 1.0.0
author: Hermes Agent
license: MIT
tags: [corpus, governance, workflow, skills, git, pull-requests, approval-gates]
---

# Corpus Change Governance

**Hard gate workflow for ANY mutation of the Hermes skill corpus** (`~/.hermes/skills/`).
This skill MUST be loaded and followed before writing, patching, or deleting any
SKILL.md, DESCRIPTION.md, or supporting file in the corpus.

## Trigger

Any task that will modify, add, or remove files under `~/.hermes/skills/` — including
but not limited to: adding tags, fixing frontmatter, renaming skills, adding new
skills, reorganizing categories, deleting skills, or updating skill bodies.

This does NOT apply to read-only operations: scanning, searching, listing, or
viewing skills.

## The 7 Gates

### Gate 1: Read-only scan and plan

Analyze the corpus to identify every file that needs to change. Produce a concrete
plan:

- List each affected file path
- Describe the exact change (what lines, what old → new)
- Explain why the change is needed
- Note any risks (YAML structure, cross-references, category implications)

**Do NOT write anything yet.** This is reconnaissance only.

### Gate 2: Present plan and wait for approval

Present the full change plan to the user. Ask for explicit approval before
proceeding. Use the `clarify` tool if needed.

**Never skip this gate.** Even if the change seems mechanical or small —
corpus YAML edits always require approval. The user's profile says: *"never
edit live corpus/YAML without approval."*

### Gate 3: Clean worktree from origin/main

On approval, create a fresh git worktree branched from `origin/main` of
`hermes-skills-backup`:

```bash
cd /Users/miqui/development/hermes-skills-backup
git fetch origin
git worktree add ../hsb-worktree-<branch-name> -b <branch-name> origin/main
```

**Never work in the primary checkout.** The user's profile says: *"always start
from a fresh git worktree on `origin/main`, not the primary checkout."*

The worktree contains the last committed snapshot under
`snapshots/<latest>/profiles/default/skills/`. Edit the files there.

### Gate 4: Edit in the worktree

Make all edits to the snapshot copy in the worktree — never to the live
`~/.hermes/skills/` directory directly.

- Use `patch` or `write_file` on the worktree copies
- Validate YAML frontmatter after every edit (parse with PyYAML)
- If creating a new snapshot is needed, use `hsb-snapshot` from the worktree

### Gate 5: Validate the snapshot

Run the backup validation suite:

```bash
cd /Users/miqui/development/hermes-skills-backup
.venv/bin/hsb-snapshot --no-secrets-check   # if a new snapshot was created
.venv/bin/hsb-validate --snapshot-id <snapshot-id>
```

Validation must return `OK` (0 errors). Warnings from pre-existing secret-detection
false positives on documentation/example files are acceptable — confirm they are
not from your changes.

### Gate 6: Push and open PR via git-workflow.sh

Commit the changes, then push and create the PR using the wrapper script —
**never raw git push**:

```bash
/Users/miqui/development/scripts/git-workflow.sh
```

The user's memory says: *"repository creation, pushing commits, and creating
pull requests must always and only use `/Users/miqui/development/scripts/git-workflow.sh`.
If that script fails, do not attempt workarounds; only report the problem."*

**The PR must be opened BEFORE the push lands.** The workflow is:
1. Commit locally in the worktree
2. Use `git-workflow.sh` to push the branch and open the PR
3. Report the PR URL to the user

**Never push directly to `main`.** Never push a branch without an associated PR.
The user's memory says: *"a snapshot commit must ALWAYS be delivered through a
GitHub pull request — never pushed directly to main or merged without a PR."*

### Gate 7: Sync to live corpus after merge

Only after the PR is reviewed and merged:
1. Pull `origin/main` in the primary checkout
2. Sync the merged snapshot back to `~/.hermes/skills/` using `hsb-restore`
3. Verify the live corpus matches the committed snapshot

**Do not sync before merge.** The live corpus should only reflect approved,
merged changes.

## Pitfalls

- **Do not edit `~/.hermes/skills/` directly and then back-fill a PR.** This is
  the anti-pattern that this skill exists to prevent. The live corpus is the
  production environment; the git repo is the review gate.

- **Do not skip the approval gate** even for "mechanical" changes like adding
  tags or fixing typos. The user explicitly requires approval for corpus YAML.

- **Do not use raw `git push` or `gh pr create` directly.** Always go through
  `git-workflow.sh`. If it fails, report the failure — do not work around it.

- **Do not create branches with `+` in the name.** The user's memory notes that
  `git-workflow.sh init` fails for directory names containing `+` due to slug
  normalization.

- **Do not push without a PR.** The push and the PR creation are a single
  atomic step via `git-workflow.sh`.

- **Do not forget to sync after merge.** If the PR is merged but the live corpus
  is not updated, the corpus and the backup diverge silently.

## Quick reference: the gates as a checklist

```
[ ] 1. Read-only scan — analyzed corpus, prepared change plan
[ ] 2. Approval — presented plan, user said go
[ ] 3. Worktree — fresh branch from origin/main of hermes-skills-backup
[ ] 4. Edit — changes made in worktree copy, not live corpus
[ ] 5. Validate — hsb-validate returns OK (0 errors)
[ ] 6. PR — pushed and PR opened via git-workflow.sh
[ ] 7. Sync — after merge, restored snapshot to live corpus
```

If any gate is not checked, the workflow is incomplete. Do not proceed past an
unchecked gate.
