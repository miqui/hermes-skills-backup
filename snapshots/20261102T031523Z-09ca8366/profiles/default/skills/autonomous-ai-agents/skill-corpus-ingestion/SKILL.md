---
name: skill-corpus-ingestion
description: "Use when importing third-party skills into a corpus, reorganizing or relocating existing skill directories within the corpus tree, or building/validating any full-corpus snapshot (including corrective/removal-only snapshots) that must prove a scoped delta against a prior committed baseline."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skill-governance, corpus, provenance, supply-chain, review]
---

# Reviewed Skill Corpus Ingestion

Use this skill when an external or locally sourced skill must become a **reviewable corpus artifact**. The default output is a pinned, auditable proposal and full-corpus snapshot—not an immediate modification of the live installed corpus.

See [pinned artifact preparation](references/pinned-artifact-preparation.md) for command-level evidence to collect during an import.

For corpus-wide tag audits (finding untagged skills, fixing the `metadata.tags` misnesting bug, improving sparse tags for search discoverability), see [corpus tag audit](references/corpus-tag-audit.md).

## Operating principles

1. **Follow the active deliverable.** If the user narrows scope (for example, from future pipeline design to a current corpus PR), immediately stop tangential work, restate the narrowed artifact, and update the task graph before dispatching further workers.
2. **Separate proposal, approval, and installation.** A PR proposes an artifact. Do not treat its existence or merge as authorization to mutate installed skills unless the user explicitly authorizes that separate action.
3. **Pin and preserve provenance.** Import only an exact upstream commit or content hash. Preserve verified author, license/copyright notice, source URL, source subtree, and immutable identifier.
4. **Use progressive disclosure.** Keep the runtime `SKILL.md` concise and route to demand-loaded references. Do not inherit foreign-agent tool declarations or eager “read everything” instructions.
5. **Keep source and native guidance distinct.** Vendor unmodified upstream material under clearly named references; write a short corpus-native entrypoint that adds only compatibility and safety normalization.

## Required gates

### 1. Scope and isolation

- Confirm the current requested artifact and exclusions before modifying files.
- If the normal checkout is dirty, work in a fresh worktree from the intended base commit; do not switch, stage, or edit the dirty checkout.
- Build a disposable overlay from a committed full-corpus baseline. Verify it is identical to that baseline before adding the proposed root.

### 2. Provenance and complete review

- Resolve the exact upstream commit SHA and selected subtree before copying content.
- Review every selected file: `SKILL.md`, references, templates, scripts, licenses, and linked commands/URLs.
- Record a file inventory and hashes for vendored source. Inspect for hidden execution, network/package mutation, secrets, broad permissions, and cross-agent residue.
- Run the approved secret scanner against the selected source and again against the normalized candidate. Keep reports redacted and record aggregate evidence only.

### 3. Normalization

The native entrypoint must:

- retain the verified upstream author and license metadata;
- state a self-contained trigger for when the skill applies;
- map task types to relevant references and load only the required ones;
- omit broad `allowed-tools` declarations and foreign-platform controls;
- make shell, network, package-management, repository, and filesystem mutation steps advisory and explicitly authorized;
- avoid copying unqualified upstream claims into top-level quick advice where context matters.

Add an `UPSTREAM.md` decision record containing source URL, immutable SHA, source subtree, attribution, license, normalization differences, scan evidence, review state, constraints, owner/reviewer role, and re-review triggers.

### 4. Snapshot and validation

1. Add the normalized skill to the isolated overlay only.
2. Generate a normal full-corpus snapshot using the repository’s canonical tool.
3. Verify the delta contains only intended roots and generated manifest/readme artifacts.
4. Validate the generated snapshot, run the repository test suite, and perform the candidate secret scan.
5. Have an independent review lane verify source-hash preservation, provenance record, native-entrypoint restrictions, test results, and snapshot delta.

### 5. Publication and installation

- Use only the repository’s required Git workflow to create branches, commits, pushes, and PRs.
- Publish a PR with concise evidence: source pin, normalized changes, snapshot ID, scan result, validation/test results, and explicit statement that the live corpus was not modified.
- Wait for the required review/approval gate before installation.
- After an explicitly authorized installation, create the normal full-corpus snapshot record if the repository’s process requires it.

## Decision outcomes

- **Proposed / pending review:** artifact is stored in a PR but not approved for installation.
- **Approved with constraints:** only the pinned artifact is permitted; no automatic installation or unauthorised command execution; re-review on any source, command, link, permission, or scope change.
- **Quarantined or rejected:** use when provenance, full-directory review, authority minimization, or hidden-execution review fails.

## Common pitfalls

- Do not import a moving branch, GitHub default branch, or latest release tag as an immutable source.
- Do not scan only the top-level skill file; risky instructions often appear in references.
- Do not claim a successful end-to-end ingestion workflow until snapshot validation, tests, independent review, and publication evidence all exist.
- Do not let work on a future automation design delay or replace the user’s concrete current PR request.
- **The snapshot tool's built-in secrets pre-scan is corpus-wide, not skill-scoped.** If the overlay is a full copy of an existing corpus, `hsb-snapshot` will abort on pre-existing, unrelated secret-like patterns anywhere in the overlay (e.g. doc placeholders in other skills), even when the new/changed skill itself is clean. When that happens: (1) run Betterleaks directly against just the new skill's final path first to get an isolated clean/dirty verdict for the artifact under review, (2) re-run `hsb-snapshot` with `--no-secrets-check` to produce the snapshot, (3) immediately run `hsb-validate` on the resulting snapshot ID — it re-scans and reports the same warnings per-file/per-category without blocking, so you get the authoritative categorized list to confirm none of the warnings land inside the new skill's directory. Do not skip step 3 just because step 2 succeeded.
 - **Routine full-corpus backup (no new skill being imported):** The isolated-scan step (1) above doesn't apply — there is no "new skill path" to scan. Instead: run Betterleaks against the entire live `~/.hermes/skills` tree with `--exit-code 0 -f json -r <file>`, confirm all hits are from broad rules (e.g. `generic-api-key`) against documentation/example files, spot-check representative hits (`sk-...` placeholders, `AKIAIO...MPLE` teaching examples, `Bearer sk-xxx...xxxx` in doc snippets), then proceed with `--no-secrets-check` + `hsb-validate`. Note: without `--validation`, the `ValidationStatus` field is absent in the JSON — 0 "validated" findings means validation wasn't performed, not that secrets were confirmed invalid. The real justification is: all hits are broad-rule pattern matches in doc/example files, confirmed by spot-checking, and `hsb-validate` reports 0 errors with only the same known warning set.
 - **Before invoking `--no-secrets-check`, prove zero *new* warning pairs, not just "some warnings exist both times."** Run `hsb-validate` on the last committed baseline snapshot and separately trigger the (aborting) `hsb-snapshot` preflight against the live/candidate source. Normalize both outputs to a comparable `relative/path [category]` form — one run emits `.../snapshots/<id>/profiles/default/...`, the other emits an absolute `--hermes-home` path — strip each down to the common `skills/...` suffix (`sed`/`grep` on the bracketed category tag), `sort -u` both lists, and `diff`/`comm -13` them. Only grant the exception when the sets are byte-identical (0 new pairs); if not, every new pair needs individual placeholder-vs-secret triage per the `secret-scan-triage` skill before proceeding.
- **`MANIFEST.json` is not a flat file-keyed map** — its top level is just `{created_utc, generator, profiles, schema_version, snapshot_id}`; per-file hashes are nested under `profiles.<name>...`, not exposed as top-level keys. Grepping/counting top-level manifest keys for a "changed file count" silently returns 0 and is wrong. Instead, get the changed-file list and count directly from the snapshot trees: `diff <(find <baseline>/profiles/<profile> -type f | sed 's#<baseline>/##' | sort) <(find <new>/profiles/<profile> -type f | sed 's#<new>/##' | sort)` — `<` lines are removed, `>` lines are added, and the line count is the exact changed-file count. This is also the correct way to run a **scope gate**: for a corrective/removal-only snapshot, the diff's `>` (added) side must be empty (or contain only the expected new artifacts) — any unexpected `>` entries mean the live corpus drifted beyond the stated correction and the snapshot must not be staged until that's reconciled with the user.
- To report an exact "changed path count" for a snapshot, grep `MANIFEST.json` for the new skill's directory name rather than diffing whole snapshots — every vendored/added file for that skill appears as its own manifest key, giving a precise, verifiable count.

## Corpus directory reorganization

When the user asks to reorganize, regroup, or move existing skill directories within the `~/.hermes/skills/` tree (not import or remove, just relocate):

### Steps

1. **Inventory first.** Use `search_files` or `find` to list every `SKILL.md` under the source category path. Group skills by proposed destination before moving anything.
2. **Present the plan before executing.** List every skill, its source path, proposed destination path, and any borderline skills that need a user decision. Do not move files until the user confirms.
3. **Check for breakage before moving.**
   - `cronjob action=list` — no cron jobs should reference skills by directory path.
   - Grep all `.md` files under `~/.hermes/skills/` for skill names being moved — `related_skills` in frontmatter uses short names (e.g. `aws-iam`), not paths, so cross-references survive a directory move. But if any file references the full directory path, note it.
4. **Move with `mv`, not copy-then-delete.** Preserves git history and file metadata. Create the target directory (`mkdir -p`) before moving.
5. **Update taxonomy references in moved skills.** Many corpus skills have a line like `adapted from ... into Hermes-native skill format for the local \`iac\` taxonomy.` Use `sed` or `patch` to update the taxonomy name in the overview prose of each moved `SKILL.md` to reflect the new path (e.g. `iac` → `iac/cloud/aws`). This is prose only — do **not** change the `name:` field in frontmatter (it's the short name used for skill resolution and `related_skills`).
6. **Verify after move.** Confirm every moved directory has its `SKILL.md`, `references/`, and other support files intact. Count `SKILL.md` files in the new location vs. the number moved.
7. **Take a post-reorg backup snapshot.** Run the canonical snapshot tool (`hsb-snapshot`) immediately so the reorg is captured in the backup repo. See the snapshot/backup pitfalls below for the `--no-secrets-check` triage flow.
8. **Deliver via PR.** Use the repository's required git workflow script (e.g. `git-workflow.sh change`) to create a branch and PR — do not commit directly to main.

### Pitfalls specific to reorg

- **Don't change `name:` fields.** The frontmatter `name` is the short identifier Hermes resolves skills by. Moving `iac/aws-iam` to `iac/cloud/aws/aws-iam` changes the display path but the `name: aws-iam` stays the same, so `skill_view(name='aws-iam')` and `related_skills: [aws-iam]` still work.
- **Do update taxonomy prose.** The line `for the local \`iac\` taxonomy` in overview sections becomes stale after a move. Update it to match the new path so future readers understand where the skill lives.
- **Count mismatch is usually a miscount, not a missing skill.** If you planned N moves but executed N-1, check whether one of the planned names was actually a skill you decided to keep (e.g. `amazon-bedrock` has an `aws-`/`amazon-` prefix but was intentionally left at `iac/` as AI/ML). Verify by listing the final directory tree, not by recounting the plan.
- **Borderline skills need a user decision.** Skills that are AWS but not infrastructure (SDK usage, AI/ML services, vector stores) don't automatically go into `iac/cloud/aws/`. Present the borderline set and ask the user where they belong before moving.
- **`metadata.tags` is not read by Hermes — use `metadata.hermes.tags` or top-level `tags`.** Some external skill registries use `metadata.tags` as their convention. Imported skills carrying that path appear untagged to Hermes despite having tags in the file. During normalization, always verify tags are at `metadata.hermes.tags` (preferred) or top-level `tags` (fallback). See [corpus tag audit](references/corpus-tag-audit.md) for the full scan methodology.
- **Tags do not affect system-prompt skill routing.** The `<available_skills>` index the LLM sees at turn time is built from skill name + description only. Tags power `hermes skills search` and `skills_list` filtering. To improve automatic skill selection, invest in the description (first 57 chars are the trigger window). To improve explicit search discoverability, invest in tags.
