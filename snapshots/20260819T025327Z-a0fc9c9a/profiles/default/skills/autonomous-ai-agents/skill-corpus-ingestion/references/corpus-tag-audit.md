# Corpus Tag Audit

Use this reference when auditing or improving tag coverage across the installed
skill corpus. Tags are not cosmetic — they power `hermes skills search`, the
`skills_list` tool filtering, and the skills catalog website. A skill with zero
tags is invisible to explicit search even if its description would match.

## How Hermes reads tags

Hermes checks two locations, in order:

1. `metadata.hermes.tags` (agentskills.io convention — preferred)
2. Top-level `tags` (fallback)

The path `metadata.tags` — **without** the `hermes` nesting — is NOT read.
This is a common import artifact: some external skill registries use
`metadata.tags` as their convention. A skill with tags at that path appears
untagged to Hermes despite having tags in the file.

### How to verify in a scan

```python
import yaml
from pathlib import Path

skills_root = Path("~/.hermes/skills").expanduser()

def get_tags(fm):
    if fm is None:
        return []
    tags = fm.get("tags", [])
    if not tags:
        meta = fm.get("metadata", {})
        if isinstance(meta, dict):
            hm = meta.get("hermes", {})
            if isinstance(hm, dict):
                tags = hm.get("tags", [])
    return tags or []

for skill_md in sorted(skills_root.rglob("SKILL.md")):
    content = skill_md.read_text(encoding="utf-8", errors="replace")
    parts = content.split("---", 2)
    fm = yaml.safe_load(parts[1]) if len(parts) >= 3 else None
    tags = get_tags(fm)
    if not tags:
        print(f"  UNTAGGED: {skill_md.relative_to(skills_root)}")
```

## How tags relate to skill routing

The `<available_skills>` index injected into the system prompt is built from
**skill name + description only**. Tags are NOT part of the routing signal the
LLM sees at turn time. This means:

- To improve whether the LLM picks the right skill automatically, invest in
  the **description** (keep the trigger class in the first 57 chars — long
  descriptions are truncated there in the system prompt index).
- To improve discoverability through explicit search (`hermes skills search`,
  `skills_list` filtering), invest in **tags**.
- Both matter; they serve different discovery paths.

Source of truth: `agent/prompt_builder.py::build_skills_system_prompt()` renders
the index; `tools/skills_tool.py` line ~1463 reads tags with the
`metadata.hermes.tags` → top-level `tags` fallback.

## Audit methodology

1. **Scan all SKILL.md files** using the script above. Report the count of
   untagged skills and the total.
2. **For each untagged skill**, read its name, description, and category path.
   Assign 5-9 tags that cover:
   - The primary technology or domain (e.g. `terraform`, `argocd`, `python`)
   - The task class (e.g. `best-practices`, `troubleshooting`, `code-review`)
   - Key search synonyms users might type (e.g. `shell` for `bash`, `k8s` for
     `kubernetes`)
   - The corpus category if not obvious from the name (e.g. `iac`, `devops`)
3. **For skills with sparse tags (3-4)**, evaluate whether key search terms
   are missing. Expand to 8-9 tags only when the existing set lacks obvious
   synonyms or domain keywords.
4. **Check for the `metadata.tags` misnesting bug.** Search for skills that
   have a `metadata:` block with a `tags:` key directly under it (not under
   `hermes:`). Those tags are invisible to Hermes. Fix by moving to top-level
   `tags:` or properly nesting under `metadata.hermes.tags:`.
5. **Verify after patching.** Re-run the scan to confirm 0 untagged skills.
   Spot-check a sample of edited files to confirm YAML parses correctly.

## Tag placement when adding to frontmatter

When a skill has no `metadata.hermes` block, prefer adding a top-level
`tags:` line — it's simpler and equally valid:

```yaml
---
name: my-skill
description: Use when ...
tags: [tag1, tag2, tag3]
---
```

When a skill already has `metadata.hermes` with other keys (e.g.
`related_skills`, `category`), add tags there to keep the metadata block
coherent:

```yaml
metadata:
  hermes:
    tags: [tag1, tag2, tag3]
    related_skills: [other-skill]
```

## Sparse-tag improvement criteria

Not every 4-tag skill needs more tags. Expand when:

- The existing tags are all variants of the same word (e.g. `[MCP, Tools,
  Integrations]` — no protocol-level synonyms like `stdio`, `http`,
  `model-context-protocol`)
- The skill covers a broad domain but tags only name the tool (e.g.
  `[Airtable, Productivity, Database, API]` — missing `REST`, `crud`,
  `automation`, `no-code`)
- Users searching for a common synonym would miss the skill (e.g. `shell` for
  `bash`, `k8s` for `kubernetes`, `oauth2` for `oauth`)

Do NOT expand when the existing tags already cover the domain well and
additional tags would just be noise.
