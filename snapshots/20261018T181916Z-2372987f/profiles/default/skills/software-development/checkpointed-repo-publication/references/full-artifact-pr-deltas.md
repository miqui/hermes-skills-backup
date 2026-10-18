# Full artifact PR deltas

Use this pattern when an artifact must remain complete and standalone, but its
PR diff is too large to review directly.

## Decision rule

Keep the complete artifact when its verifier/restore/consumer requires an
exact self-contained tree. Typical signals:

- a manifest hashes every file and rejects missing or extra files;
- restore consumes one artifact directory without a base chain;
- the repository treats each artifact as an immutable historical record.

Do not replace this with a delta-only commit unless the project is explicitly
redesigned for base-plus-delta or content-addressed storage.

## Delta algorithm

1. Locate the current and immediately preceding artifact IDs in deterministic
   chronological order.
2. Load their manifests; compare file entries by `(scope/profile, relative
   path)` and hash/size metadata.
3. Discover owning units from descriptor files (for skills, each `SKILL.md`
   directory).
4. Map changed files to the deepest containing unit across both artifacts.
5. Classify units as added, modified, or removed. Report changed files that do
   not belong to a descriptor unit under `Unscoped files`.
6. Render a short Markdown comment that names the base artifact and explicitly
   says the full artifact remains for restore/integrity.

Never render secret values or scanner match contents. Paths and non-sensitive
classification labels are sufficient for reviewer triage.

## GitHub Actions publication

- Detect changed artifact manifests from the PR base/head diff.
- Keep normal test and changed-artifact validation on every `pull_request`.
- For same-repository PRs only, grant a dedicated comment job the smallest
  write scope it needs and upsert a comment using a stable HTML marker.
- Skip comment writes for fork PRs. Do not switch to `pull_request_target` to
  obtain a write token while checking out or executing PR-controlled code.
- Make the comment job conditional on actual artifact changes, so pipeline or
  documentation PRs do not receive irrelevant delta comments.

## Verification

- Unit-test added, modified, removed, and unscoped classifications.
- Unit-test both creating and updating the marker-owned comment.
- Render the report against a real known artifact pair and compare its listed
  units with an independent file-level diff.
- Verify workflow syntax and run the full local test suite.
- After merge, verify one actual artifact PR creates exactly one marker-owned
  comment and reruns update that comment instead of duplicating it.
