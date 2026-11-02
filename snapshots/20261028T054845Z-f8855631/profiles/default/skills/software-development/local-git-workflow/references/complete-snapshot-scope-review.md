# Complete Snapshot Scope Review

Use this before publishing a full, standalone corpus snapshot when the user approved a bounded change but the installed corpus may also contain older local edits.

## Why it matters

A valid `hermes-skills-backup` snapshot is a complete profile tree. Do not hand-prune it to hide unrelated installed changes: that breaks the restore and verification contract. The review unit is therefore the **manifest delta**, not merely the newly authored file.

## Procedure

1. Capture and validate the complete snapshot normally.
2. Compare its `MANIFEST.json` with the latest merged snapshot manifest.
3. Report added, modified, and removed paths grouped by skill root. Do not report file contents or secret-scanner match values.
4. Classify every changed skill root as either:
   - within the user's approved scope;
   - an earlier, independent corpus change; or
   - unexplained.
5. If independent or unexplained roots exist, pause before staging and ask for one explicit decision:
   - include all current corpus changes in this checkpoint;
   - defer publication until the other changes are reviewed separately; or
   - explicitly restore the unrelated installed files to the prior approved state, then capture a new snapshot.
6. Stage only the resulting full `snapshots/<id>/` directory. Verify all staged paths are under that ID and that no unstaged repository changes remain before the publication wrapper runs.

## Safety constraints

- Never silently omit paths from a complete snapshot.
- Never revert installed corpus files without explicit approval; they may represent valid work from another session.
- If the user approves inclusion, name the unrelated skill roots in the PR summary so reviewers see the real delta.
- Keep secret-scanner comparisons value-safe: use path/category metadata, not matched values.
