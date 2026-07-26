# High-Confidence Catalog Curation Patterns

Use this note when cleaning a local Hermes skill library after imports, taxonomy moves, or duplicate absorption work.

## Recommended pass order

Run the cleanup in this order so each pass reduces noise for the next one:

1. **Duplicate-cluster consolidation**
   - Only merge high-confidence overlaps where one skill is clearly the umbrella.
   - Patch the umbrella skill first so must-preserve guidance is not lost.
   - Delete absorbed skills with `skill_manage(action='delete', absorbed_into='<umbrella>')` so the curator can track intent.
   - Immediately re-scan for stale references to the absorbed names.

2. **Broken `related_skills` audit**
   - Build the set of valid local skill names from all `SKILL.md` directories.
   - Remove superseded legacy names instead of inventing redirects.
   - Replace renamed skills only when the new canonical local name is clear.

3. **Metadata hardening for imported clusters**
   - When a bulk import leaves many narrow siblings in place, improve routing before restructuring.
   - Tighten `metadata.hermes.tags` so each skill carries service-specific terms, not just generic import residue.
   - Add high-confidence `related_skills` links from narrow imported skills to existing umbrella skills and to their closest sibling specialists.
   - Use this pass when the user wants better selection quality without taxonomy moves or merges.
   - If the user chooses this as a numbered follow-up option, do not collapse it into consolidation; treat it as a distinct pass.

4. **Directory/frontmatter name normalization**
   - Prefer renaming the directory to match the canonical frontmatter `name` when no references to the old slug remain and no destination collision exists.
   - Re-audit after each rename batch.

5. **Imported-residue cleanup**
   - Start with the highest-confidence residue: invalid foreign install flows, wrong local directories, or obsolete wrapper commands.
   - Preserve provenance when you remove imported install steps: replace them with a short upstream-note section instead of deleting attribution.
   - Do not "clean" legitimate product documentation just because it names another ecosystem.

6. **Stale internal reference cleanup**
   - Search for exact `skill_view("old-name")` calls, `skills/<old-slug>/...` paths, and explicit prose like "load X skill".
   - Patch those immediately after moves, deletions, or absorptions.

## Search strategy that avoids false positives

Do **not** start with a raw word search for deleted names that are also normal English terms.

Examples:
- `domain`
- `build`
- `style`

These terms will flood the results with legitimate content.

Instead, search in increasingly broad layers:
1. exact `skill_view(...)` calls
2. old `skills/<slug>` paths
3. explicit skill-invocation prose (`load X skill`, `use X skill`, `pair with X`)
4. only then, if still needed, broader text searches with manual review

## Practical stopping rule

Stop when:
- the scripted audits are clean, or
- the remaining hits are clearly provenance/history notes rather than live instructions

Example of a safe remaining mention:
- "This skill supersedes `old-skill-name`" as historical context

That is not the same as a broken load instruction.
