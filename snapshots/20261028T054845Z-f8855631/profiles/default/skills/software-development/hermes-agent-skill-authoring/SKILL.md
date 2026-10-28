---
name: hermes-agent-skill-authoring
description: "Author in-repo SKILL.md: frontmatter, validator, structure."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, authoring, hermes-agent, conventions, skill-md]
    related_skills: [writing-plans, requesting-code-review]
---

# Authoring Hermes-Agent Skills (in-repo)

## Overview

There are two places a SKILL.md can live:

1. **User-local:** `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — personal, not shared. Created via `skill_manage(action='create')`.
2. **In-repo (this skill is about this case):** `/home/bb/hermes-agent/skills/<category>/<name>/SKILL.md` — committed, shipped with the package. Use `write_file` + `git add`. `skill_manage(action='create')` does NOT target this tree.

## When to Use

- User asks you to add a skill "in this branch / repo / commit"
- You're committing a reusable workflow that should ship with hermes-agent
- You're editing an existing skill under `/home/bb/hermes-agent/skills/` (use `patch` for small edits, `write_file` for rewrites; `skill_manage` still works for patch on in-repo skills, but not for `create`)

## Required Frontmatter

Source of truth: `tools/skill_manager_tool.py::_validate_frontmatter`. Hard requirements:

- Starts with `---` as the first bytes (no leading blank line).
- Closes with `\n---\n` before the body.
- Parses as a YAML mapping.
- `name` field present.
- `description` field present, ≤ **1024 chars** (`MAX_DESCRIPTION_LENGTH`).
- Non-empty body after the closing `---`.

Peer-matched shape used by every skill under `skills/software-development/`:

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars (MAX_NAME_LENGTH)
description: Use when <trigger>. <one-line behavior>.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

`version` / `author` / `license` / `metadata` are NOT enforced by the validator, but every peer has them — omit and your skill sticks out.

## Size Limits

- Description: ≤ 1024 chars (enforced).
- Full SKILL.md: ≤ 100,000 chars (enforced as `MAX_SKILL_CONTENT_CHARS`, ~36k tokens).
- Peer skills in `software-development/` sit at **8-14k chars**. Aim for that range. If you're pushing past 20k, split into `references/*.md` and reference them from SKILL.md.

## Peer-Matched Structure

Every in-repo skill follows roughly:

```
# <Title>

## Overview
One or two paragraphs: what and why.

## When to Use
- Bulleted triggers
- "Don't use for:" counter-triggers

## <Topic sections specific to the skill>
- Quick-reference tables are common
- Code blocks with exact commands
- Hermes-specific recipes (tests via scripts/run_tests.sh, ui-tui paths, etc.)

## Common Pitfalls
Numbered list of mistakes and their fixes.

## Verification Checklist
- [ ] Checkbox list of post-action verifications

## One-Shot Recipes (optional)
Named scenarios → concrete command sequences.
```

Not every section is mandatory, but `Overview` + `When to Use` + actionable body + pitfalls are the minimum for the skill to feel like a peer.

## Directory Placement

```
skills/<category>/<skill-name>/SKILL.md
```

Categories currently in repo (confirm with `ls skills/`): `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `dogfood`, `email`, `gaming`, `github`, `leisure`, `mcp`, `media`, `mlops/*`, `note-taking`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `software-development`.

Pick the closest existing category. Don't invent new top-level categories casually.

## Workflow

1. **Survey peers** in the target category:
   ```
   ls skills/<category>/
   ```
   Read 2-3 peer SKILL.md files to match tone and structure.
2. **Check validator constraints** in `tools/skill_manager_tool.py` if unsure.
3. **Draft** with `write_file` to `skills/<category>/<name>/SKILL.md`.
4. **Validate locally**:
   ```python
   import yaml, re, pathlib
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---")
   m = re.search(r'\n---\s*\n', content[3:])
   fm = yaml.safe_load(content[3:m.start()+3])
   assert "name" in fm and "description" in fm
   assert len(fm["description"]) <= 1024
   assert len(content) <= 100_000
   ```
5. **Git add + commit** on the active branch.
6. **Note:** the CURRENT session's skill loader is cached — `skill_view` / `skills_list` will not see the new skill until a new session. This is expected, not a bug.

## Cross-Referencing Other Skills

`metadata.hermes.related_skills` unions both trees (`skills/` in-repo and `~/.hermes/skills/`) at load time. You CAN reference a user-local skill from an in-repo skill, but it won't resolve for other users who clone the repo fresh. Prefer referencing only in-repo skills from in-repo skills. If a frequently-referenced skill lives only in `~/.hermes/skills/`, consider promoting it to the repo.

## Editing Existing In-Repo Skills

- **Small fix (typo, added pitfall, tightened trigger):** `skill_manage(action='patch', name=..., old_string=..., new_string=...)` works fine on in-repo skills.
- **Major rewrite:** `write_file` the whole SKILL.md. `skill_manage(action='edit')` also works but requires supplying the full new content.
- **Adding supporting files:** `write_file` to `skills/<category>/<name>/references/<file>.md`, `templates/<file>`, or `scripts/<file>`. `skill_manage(action='write_file')` also works and enforces the references/templates/scripts/assets subdir allowlist.
- **For manually added or imported skills:** run a review pass for inherited environment-specific residue, missing frontmatter, broken skill references, and directory/frontmatter naming mismatches. If the user added multiple skills, triage the newest `SKILL.md` files by modification time first so review effort lands on the actual manual additions. When locating a freshly added user-local skill, do not rely on a wildcard filename search alone; enumerate recent `~/.hermes/skills/**/SKILL.md` files directly and inspect the newest paths, because some searches miss the directory slug while the skill itself still exists. See `references/manual-skill-review-checklist.md` and `references/imported-skill-normalization.md`.
- **If the user says to use/refactor the new skills they added, treat that as an in-place refactor order, not permission to create replacement siblings.** Inspect the newest skill directories in the target taxonomy area first, confirm which ones are the recent manual additions, and normalize those exact skills before considering any new skill creation. Only create a new sibling when there is a genuinely missing class-level gap after the user-added skills have been evaluated.
- **When normalizing an imported skill:** prefer rewriting the full `SKILL.md` into Hermes-native shape rather than doing many tiny patches. First align the canonical local name (directory + frontmatter `name`), then rewrite the main file, then scan and update any linked `references/*.md` files in the same pass so stale external skill references do not survive in support files. Also inspect root-level sibling docs in the skill directory, not just `references/`; manually added skills sometimes leave helpers like `variables.md` beside `SKILL.md` while the main file links to `references/variables.md`, creating a silent broken-reference mismatch unless you compare the links against the actual files on disk.
- **For user-local imported skills under `~/.hermes/skills/`:** use the same normalization workflow even though the skill is not in-repo. Rewrite the main `SKILL.md`, normalize frontmatter to the Hermes peer shape (`name`, `description`, `version`, `author`, `license`, `metadata.hermes.tags`, `metadata.hermes.related_skills`), then inspect support files for stale upstream references before calling the cleanup complete.
- **For taxonomy cleanup, prefer a minimal high-confidence pass over a sweeping reorg.** Move only obvious root-level outliers into already-existing categories, convert category stubs that actually contain skill frontmatter into real `SKILL.md` files under the closest existing category, and delete empty taxonomy-only stub directories that advertise categories or skills with no actual content. Avoid speculative moves for borderline cases until a second pass.
- **Normalize near-miss category names before deeper review.** Manually added user-local skills sometimes land under a singular/plural variant of an existing category (for example `local-util` when the intended bucket is `local-utils`). If the intended taxonomy is clear, rename the directory to the canonical category first, then verify Hermes discovery with `skills_list(category=...)` before doing content cleanup so later patches target the stable path.
- **After moving or deleting categories, run a stale-reference pass immediately.** Search the whole skill tree for `skill_view("old-name")`, in-body "load X skill" guidance, and category names that used to behave like skills. Patch those references to concrete surviving skills (for example `excalidraw` instead of a removed `diagramming` stub) before declaring the taxonomy cleanup complete.
- **Verify support-file reality, not just support-file names.** Imported skills often point at helpers that almost exist but not quite — for example `.yaml` names when the local assets are actually `.md`, references to unavailable tools such as `present_files`, or hard-coded output paths copied from another runtime. During normalization, compare the main `SKILL.md` against the actual files in `references/`, `templates/`, `scripts/`, and `assets/`, then patch both the main file and the linked support docs so the whole skill directory is self-consistent.
- **When a user provides an external article or doc to harden a manually added skill, distill it into a local support file instead of leaving the guidance as a bare link or dumping it inline.** Create a concise `references/<topic>.md` that captures the source, the applicable takeaways, and any caveats; then patch the relevant operational reference file (for example `references/troubleshooting.md`) and, if useful, add a one-line pointer from the main `SKILL.md`. This keeps imported/manual skill fixes Hermes-native and preserves the reasoning behind why the source mattered.
- **When a broad skill embeds local host policy, split it out instead of keeping it inline.** If a portable implementation skill (for example, a language or framework skill) contains machine-specific Git, repo-location, wrapper-script, or host-policy rules, extract those rules into a dedicated local workflow skill such as `local-git-workflow`. Then patch the broad skill to reference that local workflow skill in `related_skills`, overview/when-to-use guidance, pitfalls, and verification checklists. Keep the broad skill portable; keep the environment policy explicit but isolated.
- **When verifying residue cleanup:** search the entire skill directory, but remember that verification checklists can accidentally mention the old ecosystem names you just removed. If a checklist line itself triggers the residue search, rewrite or delete that checklist item instead of treating it as a content false positive.
- **Imported-residue verification pass:** after rewriting, run a directory-wide content search for common upstream leftovers such as `samber/cc-skills`, `openclaw`, `Claude Code`, `allowed-tools`, `AskUserQuestion`, `WebFetch`, `WebSearch`, `mcp__context7__`, `compatibility:`, `Persona:`, `Modes:`, `Community default`, and `ultrathink`. Then run a second search for stale cross-skill references that no longer exist locally. This catches both imported wrapper text and broken related-skill pointers.
- **For catalog integrity cleanup, run scripted whole-tree audits instead of spot checks.** Audit at least broken `related_skills`, directory/frontmatter `name` mismatches, and stale references after deletions or absorptions. See `references/catalog-integrity-audits.md` for the compact playbook.
- **For multi-pass local catalog cleanup, follow the proven pass order in `references/catalog-curation-patterns.md`.** Start with duplicate consolidation, then broken `related_skills`, then name normalization, then imported-residue cleanup, and finish with stale internal references. This ordering reduces noise between passes.
- **Treat metadata hardening as a first-class cleanup pass when bulk-importing many narrow skills.** Before merging siblings, consider a lower-risk pass that sharpens `metadata.hermes.tags` and `related_skills` across the imported cluster so routing improves without changing taxonomy. This is especially useful when the user wants to keep imports as siblings for now but still reduce skill-selection noise.
- **When the user picks one numbered cleanup option from your own proposed list, execute that exact option only.** Do not silently reinterpret it as a neighboring cleanup mode (for example, starting consolidation when the user chose metadata tuning). If the option wording is yours, the burden is on you to honor it precisely.
- **When auditing stale references, avoid raw word searches for deleted names that are also ordinary English terms.** Search exact `skill_view(...)` calls, old `skills/<slug>` paths, and explicit "load/use/pair with X skill" prose before doing broader text searches, or you'll drown in false positives from words like `domain`, `build`, or `style`.
- **When directory and frontmatter names disagree, prefer renaming the directory to the canonical frontmatter name when safe.** Only do this after verifying there are no live references to the old slug and no destination collision; otherwise patch the frontmatter instead.
- **Always commit** the edit — in-repo skills are source, not runtime state.

## Common Pitfalls

1. **Using `skill_manage(action='create')` for an in-repo skill.** It writes to `~/.hermes/skills/`, not the repo tree. Use `write_file` for in-repo creation.

2. **Leading whitespace before `---`.** The validator checks `content.startswith("---")`; any leading blank line or BOM fails validation.

3. **Description too generic.** Peer descriptions start with "Use when ..." and describe the *trigger class*, not the one task. "Use when debugging X" > "Debug X".

4. **Forgetting the author/license/metadata block.** Not validator-enforced, but every peer has it; omitting makes the skill look half-finished.

5. **Writing a skill that duplicates a peer.** Before creating, `ls skills/<category>/` and open 2-3 peers. Prefer extending an existing skill to creating a narrow sibling.

6. **Expecting the current session to see the new skill.** It won't. The skill loader is initialized at session start. Verify in a fresh session or via `skill_view` using the exact path.

7. **Linking to skills that don't exist in-repo.** `related_skills: [some-user-local-skill]` works for you but breaks for other clones. Prefer only in-repo links.

8. **Copying a skill from another environment without de-nanoising it.** Manually added skills often retain old workspace paths, wrapper names, MCP tool references, or branch conventions from their source environment. Review imported skills for environment-specific residue before trusting them.

9. **Leaving the frontmatter `name` out of sync with the directory name.** Imported skills often arrive with a canonical name from another registry (`golang-swagger`, `golang-code-style`, etc.) while the local directory uses a different slug. Normalize one canonical local name and make the directory, frontmatter `name`, and related-skill references agree.

10. **Cleaning the main SKILL.md but forgetting linked reference files.** Imported residue often survives in `references/*.md` after the main file is rewritten. Re-scan support files for stale external skill names, agent/tool references, obsolete ecosystem metadata, mismatched file extensions, and imported delivery assumptions such as nonexistent handoff tools or hard-coded output directories.

## Verification Checklist

- [ ] File is at `skills/<category>/<name>/SKILL.md` (not in `~/.hermes/skills/`)
- [ ] Frontmatter starts at byte 0 with `---`, closes with `\n---\n`
- [ ] `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}` all present
- [ ] Name ≤ 64 chars, lowercase + hyphens
- [ ] Description ≤ 1024 chars and starts with "Use when ..."
- [ ] Total file ≤ 100,000 chars (aim for 8-15k)
- [ ] Structure: `# Title` → `## Overview` → `## When to Use` → body → `## Common Pitfalls` → `## Verification Checklist`
- [ ] `related_skills` references resolve in-repo (or are explicitly OK to be user-local)
- [ ] `git add skills/<category>/<name>/ && git commit` completed on the intended branch
