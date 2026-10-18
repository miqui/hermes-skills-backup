# Catalog Integrity Audits for Hermes Skills

Use this when cleaning up a local skill library after imports, taxonomy moves, or duplicate consolidation.

## Why this exists

Spot checks miss catalog-wide consistency issues. A short scripted audit over every `SKILL.md` catches the highest-value integrity problems quickly:

1. broken `metadata.hermes.related_skills`
2. directory name vs frontmatter `name` mismatches
3. stale references to deleted or absorbed skills

## Audit 1: Broken `related_skills`

Build the set of valid local skill names from all `SKILL.md` paths, then parse each file's `related_skills` list and compare.

### Practical recipe

- enumerate all `SKILL.md` files under the skill root
- derive the local canonical skill name from the directory name
- parse each file's `related_skills: [...]`
- flag any referenced skill names that are not present locally

### Fix policy

- if the missing skill was clearly superseded by the current skill, **remove** the stale related skill
- if the missing skill was renamed locally, replace it with the current canonical local name
- do not invent redirects when the relationship is unclear

## Audit 2: Directory name vs frontmatter `name`

Compare the directory slug containing `SKILL.md` with the frontmatter `name` field.

### Fix policy

Prefer this order:

1. if the frontmatter `name` is already the canonical local name and no live references use the old directory slug, **rename the directory** to match the frontmatter
2. if the directory slug is the intended local canonical name, patch the frontmatter `name` instead
3. before renaming, verify there is no destination collision
4. after renaming, re-scan for stale textual references to the old slug

### High-confidence rename checklist

- frontmatter `name` already matches how the skill is referred to elsewhere
- no remaining references to the old directory slug in the skill tree
- destination directory does not already exist

## Audit 3: Stale references after deletion or consolidation

After deleting, absorbing, or moving skills, search the whole catalog for:

- `skill_view("old-name")`
- old skill names in prose such as "load X skill"
- old names in `related_skills`
- old names in linked `references/*.md`

Patch references immediately before declaring the cleanup complete.

## Tooling note

When scripting against Hermes file-search helpers, parse results defensively. Some environments return file lists under `files` instead of `matches`. Do not hard-code one response shape if you are writing a catalog-wide audit script.

## Minimal verification loop

1. run the audit
2. patch only high-confidence cases
3. re-run the same audit
4. stop when the result is clean or only ambiguous cases remain
