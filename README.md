# hermes-skills-backup

Backup, validate, verify, and restore all [Hermes Agent](https://github.com) skill
profiles as portable, host-agnostic snapshots.

A snapshot is a plain directory tree plus a `MANIFEST.json` that records a
SHA-256 hash and size for every file. It never records hostnames, absolute
source paths, OS details, or credentials — it is safe to copy, diff, or hand
to someone else.

## Requirements

- Python >= 3.9
- PyYAML (installed automatically)

## Install

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

This provides four console scripts: `hsb-snapshot`, `hsb-validate`,
`hsb-verify`, and `hsb-restore`.

## Snapshot layout

```
snapshots/<snapshot-id>/
  MANIFEST.json
  RESTORE.md
  profiles/
    default/skills/          <- from <hermes-home>/skills
    <profile-name>/skills/   <- from <hermes-home>/profiles/<profile-name>/skills
```

Every profile — including `default` — lives under `profiles/<name>/skills`
inside the snapshot, so the schema is uniform regardless of how many named
profiles a given host has. A host with no named profiles produces a snapshot
containing only the `default` profile; hosts with additional profiles under
`~/.hermes/profiles/<name>/skills` get one `profiles/<name>/skills` tree per
profile.

Hidden/internal top-level entries under each skills directory (e.g.
`.curator_backups`, `.hub`, `.usage.json`) are excluded — these are Hermes
runtime bookkeeping, not skill content. Nested hidden files that are
legitimate skill assets (e.g. a skill's own `.gitkeep` or `.golangci.yml`)
are preserved. Symlinks are never followed or included, anywhere.

## Usage

### Create a snapshot

```bash
hsb-snapshot --hermes-home ~/.hermes --output-dir snapshots
```

Add `--snapshot-id <id>` to pin the id, or `--no-secrets-check` to skip the
best-effort secrets scan (only recommended when you've already confirmed any
flagged content is a documentation placeholder, not a live credential).

### Verify integrity

`hsb-verify` checks manifest schema/types, snapshot id format, SHA-256 of
every file, and exact manifest/on-disk correspondence (no missing or extra
files).

```bash
hsb-verify --snapshots-dir snapshots --snapshot-id <id>
hsb-verify --snapshots-dir snapshots --all
```

### Full validation

`hsb-validate` runs everything `hsb-verify` does, plus: YAML frontmatter
parsing and required-field checks on every `SKILL.md`, a likely-secrets scan
(reports file path + category only, never the matched value), and a check
for forbidden internal state files/dirs anywhere in the snapshot.

```bash
hsb-validate --snapshots-dir snapshots --snapshot-id <id>
hsb-validate --snapshots-dir snapshots --all
```

### Restore

Restores are **dry-run by default**. Nothing is written unless you pass
`--apply`, and you must always name an explicit target Hermes home — there
is no default target, so you can never accidentally overwrite `~/.hermes`.

```bash
# Dry run — prints the plan, changes nothing
hsb-restore --snapshots-dir snapshots --snapshot-id <id> \
  --target-hermes-home /path/to/target

# Apply
hsb-restore --snapshots-dir snapshots --snapshot-id <id> \
  --target-hermes-home /path/to/target --apply
```

Restoring rebuilds, per profile:

- `default` → `<target-hermes-home>/skills`
- `<profile-name>` → `<target-hermes-home>/profiles/<profile-name>/skills`

The snapshot is fully re-verified before anything is staged, every file is
copied into a temporary staging directory and hash-checked again before
anything under the target is touched, and only the exact profile skills
directories being restored are ever replaced — nothing else under the
target, and nothing outside the target, is ever modified or deleted. See
[docs/branch-protection.md](docs/branch-protection.md) for the manual
restore runbook used alongside this project's GitHub branch protection.

## Development

```bash
.venv/bin/python -m pytest
```

Tests cover multi-profile capture, top-level exclusions, invalid YAML
frontmatter, tampered/mismatched manifests, dry-run vs. applied restores,
and path-traversal / symlink safety.

## License

MIT — see [LICENSE](LICENSE).
