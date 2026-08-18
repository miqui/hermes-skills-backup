# Restore Instructions

Snapshot ID: `20260818T144228Z-ed4463fd`
Created (UTC): 2026-08-18T14:42:29Z
Profiles included: default

This snapshot was produced by the `hermes-skills-backup` project and can be
restored with its `hsb-restore` command-line tool.

## Dry run (default — makes no changes)

```
hsb-restore \
  --snapshots-dir <path-to-snapshots-dir> \
  --snapshot-id 20260818T144228Z-ed4463fd \
  --target-hermes-home <path-to-target-hermes-home>
```

## Apply the restore

```
hsb-restore \
  --snapshots-dir <path-to-snapshots-dir> \
  --snapshot-id 20260818T144228Z-ed4463fd \
  --target-hermes-home <path-to-target-hermes-home> \
  --apply
```

Restoring rebuilds, per profile:

- `default` → `<target-hermes-home>/skills`
- `<profile-name>` → `<target-hermes-home>/profiles/<profile-name>/skills`

Data is staged in a temporary directory and verified before anything under
the target Hermes home is replaced. Nothing outside the target Hermes home
is ever modified or removed.

Before restoring, verify the snapshot's integrity with `hsb-verify` and
`hsb-validate`.
