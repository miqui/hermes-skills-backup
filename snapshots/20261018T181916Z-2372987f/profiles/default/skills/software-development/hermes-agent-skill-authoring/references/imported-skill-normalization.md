# Imported Skill Normalization

Use this when a skill was copied from another registry, another agent stack, or a manually curated bundle and you want to make it feel native inside Hermes.

## Typical residue markers

Look for these strings in both `SKILL.md` and linked support files:

- `openclaw`
- `Claude Code`
- `allowed-tools`
- `AskUserQuestion`
- `WebFetch`
- `WebSearch`
- `mcp__context7__`
- external skill references such as `samber/cc-skills...@...`
- takeover banners like `Community default` or other registry-precedence notes

These are strong signs the skill was imported without normalization.

## Fast normalization workflow

1. **Check name alignment first**
   - Directory name
   - Frontmatter `name`
   - In-body references to the skill

   If these disagree, fix them before anything else. Name mismatches are one of the fastest ways to make a skill hard to discover.

2. **Rewrite frontmatter into Hermes-native shape**

```yaml
---
name: my-skill-name
description: Use when ...
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tag1, tag2]
    related_skills: [peer-skill]
---
```

Remove imported fields that belong to another ecosystem unless they are still intentionally supported.

3. **Normalize the body, not just the header**
   - Add `## Overview` and `## When to Use` if absent
   - Remove registry-precedence banners and other import-only notices
   - Replace agent-specific instructions with portable Hermes guidance
   - Convert stale "see X external skill" references into local related skills or plain prose

4. **Update linked support files in the same pass**
   Imported residue often survives in `references/*.md` after the main skill is rewritten. Re-scan support files and remove stale external skill names or tool references.

   Also verify that the support-file references are *real* in the local tree:
   - filenames and extensions match what actually exists (`.md` vs `.yaml`, etc.)
   - helper scripts or templates named in `SKILL.md` are present locally
   - delivery instructions do not rely on unavailable tools such as `present_files`
   - output paths are not copied from another runtime (`/mnt/...`, container-only paths, etc.) unless they are truly valid here

   If the main skill and the support files disagree, patch both sides before calling the normalization done.

5. **Verify with a residue grep**
   Search for the marker strings above across the whole skill directory, not just `SKILL.md`.

## Example normalization pattern

A common imported-skill repair sequence is:

- directory slug says `golang-coding-style`
- frontmatter says `golang-code-style`
- body still references `samber/cc-skills-golang@...`
- support files still mention external skills

The correct repair is not just a one-line rename. Normalize the canonical name first, then rewrite the `SKILL.md` into Hermes-native structure, then clean `references/*.md`, then verify no imported residue remains.

## Good outcome

A normalized imported skill:

- loads under the expected local name
- starts its description with `Use when ...`
- uses `metadata.hermes` rather than foreign metadata blocks
- references real local skills where possible
- has support files that are just as clean as the main `SKILL.md`
