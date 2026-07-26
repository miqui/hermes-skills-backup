# Manual / Imported Skill Review Checklist

Use this when a skill was manually added, copied from another host, or imported from another agent setup.

## Review passes

0. Triage the review set first
   - If the user says they "manually added new skills", identify the newest `SKILL.md` files by modification time before opening everything
   - Review the most recently changed skills first; this usually isolates the imported/manual additions quickly
   - Separate structural issues (frontmatter, sections, naming) from semantic issues (stale references, obsolete tool names, bad local assumptions)

1. Remove inherited environment-specific residue
   - Old workspace roots like `/workspace/...`, `/app/src/...`, or container-only paths
   - Host-specific script paths that do not match the current machine
   - Provider- or tool-specific instructions that refer to unavailable MCP tools, internal wrappers, or old agent names
   - Branch-name conventions or repo workflow rules that belong to a different environment

2. Normalize skill structure
   - Add YAML frontmatter if missing
   - Ensure `name` matches the directory and is lowercase with hyphens
   - Ensure `description` starts with `Use when ...`
   - Add `version`, `author`, `license`, and `metadata.hermes.{tags, related_skills}`
   - Normalize the title and add an `## Overview` section if absent

3. Validate references
   - Check that `related_skills` actually exist
   - Check that any in-body "Use X skill" guidance points to real, loadable skills
   - Replace stale slash-command or pseudo-tool references with current equivalents
   - Verify that referenced support files, filenames, and extensions match what actually exists locally
   - Check delivery instructions for unavailable tools or borrowed runtime paths (for example `present_files` or `/mnt/...`)
   - Scan linked `references/*.md` files too, not just the main SKILL.md

4. Verify cleanup results
   - Search the whole skill directory for imported ecosystem residue (`openclaw`, scoped external skill names, obsolete tool names, old personas)
   - Prefer distinctive markers over broad generic words; avoid residue searches that match normal prose by accident (for example, a plain search for `Read` will hit legitimate sentences like `Read references/foo.md`)
   - If you must search for an ambiguous pseudo-tool name, anchor it with surrounding context or formatting so normal prose does not trigger false positives
   - If the only remaining hits are in a verification checklist or review note, rewrite that checklist text so the residue search becomes clean

5. Verify local conventions
   - Project-root paths match the current host's expected workspace
   - Git/GitHub workflow instructions match the user's actual wrapper scripts and policies
   - Communication guidance does not mention obsolete agent-specific tools or personas

## Good outcomes

- The skill is portable within the current environment
- The skill no longer leaks assumptions from a previous host or agent stack
- Related-skill guidance points only to real skills
- The file matches normal Hermes SKILL.md structure instead of a pasted persona prompt
- A residue search across the whole skill directory comes back clean
