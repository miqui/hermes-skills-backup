"""
hsb-validate — full validation of a snapshot. Covers everything hsb-verify
checks (manifest schema/types, snapshot id, SHA-256 of every file, exact
manifest/on-disk correspondence, profiles/default presence) plus:

  * valid YAML frontmatter and nonempty name/description in every SKILL.md
  * likely-secret detection (reports filepath + category only, never the
    matched value)
  * forbidden state files/dirs anywhere in the snapshot
  * unsafe symlinks / path escapes

Severity policy
----------------
Manifest schema, hashes, manifest/on-disk correspondence, path/symlink
safety, forbidden state, and invalid YAML frontmatter are always blocking
errors (nonzero exit). Likely-secret hits are reported as non-blocking
*warnings* by default: skill documentation, templates, and examples
routinely contain token/key-shaped placeholder strings (e.g. `sk-xxxx...`,
`AKIAIOSFODNN7EXAMPLE`) that a pattern match cannot distinguish from a real
leak, so they are surfaced (path + category only, never the matched value)
without failing the run. Pass --strict-secrets to instead treat every
likely-secret hit as a blocking error.

Usage
-----
    hsb-validate --snapshots-dir snapshots --snapshot-id <snapshot-id>
    hsb-validate --snapshots-dir snapshots --all
    hsb-validate --snapshots-dir snapshots --all --strict-secrets
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hermes_skills_backup.checks import has_errors, validate_snapshot
from hermes_skills_backup.common import list_snapshot_ids


def _run_one(snapshot_dir: Path, check_secrets_enabled: bool, strict_secrets: bool) -> bool:
    manifest, issues = validate_snapshot(
        snapshot_dir,
        check_secrets_enabled=check_secrets_enabled,
        strict_secrets=strict_secrets,
    )
    ok = manifest is not None and not has_errors(issues)

    print(f"Snapshot: {snapshot_dir.name}")
    if manifest is not None:
        file_total = sum(p.get("file_count", 0) for p in manifest.get("profiles", {}).values() if isinstance(p, dict))
        skill_total = sum(
            1
            for p in manifest.get("profiles", {}).values() if isinstance(p, dict)
            for rel in p.get("files", {})
            if Path(rel).name == "SKILL.md"
        )
        print(f"  profiles : {len(manifest.get('profiles', {}))}")
        print(f"  files    : {file_total}")
        print(f"  SKILL.md : {skill_total}")

    by_category: "dict[str, int]" = {}
    error_count = 0
    warning_count = 0
    for issue in issues:
        by_category[issue.category] = by_category.get(issue.category, 0) + 1
        if issue.severity == "error":
            error_count += 1
            stream = sys.stderr
        else:
            warning_count += 1
            stream = sys.stdout
        print(f"  {issue}", file=stream)

    print(
        f"  result   : {'OK' if ok else 'FAILED'} "
        f"({error_count} error(s), {warning_count} warning(s); by category: {by_category})"
    )
    print()
    return ok


def main(argv: "list[str]" = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hsb-validate",
        description="Fully validate one or more snapshots (schema, hashes, frontmatter, secrets, forbidden state).",
    )
    parser.add_argument("--snapshots-dir", type=Path, default=Path("snapshots"), metavar="DIR")
    parser.add_argument("--snapshot-id", default=None, metavar="ID")
    parser.add_argument("--all", action="store_true", default=False, help="Validate every snapshot in --snapshots-dir")
    parser.add_argument("--no-secrets-check", action="store_true", default=False, help="Skip the secrets scan")
    parser.add_argument(
        "--strict-secrets", action="store_true", default=False,
        help="Treat likely-secret hits as blocking errors instead of non-blocking warnings",
    )

    args = parser.parse_args(argv)
    snapshots_dir = args.snapshots_dir.expanduser().resolve()

    if not args.all and not args.snapshot_id:
        parser.error("either --snapshot-id or --all is required")

    if args.all:
        ids = list_snapshot_ids(snapshots_dir)
        if not ids:
            print(f"✗ No snapshots found in {snapshots_dir}", file=sys.stderr)
            return 1
    else:
        ids = [args.snapshot_id]

    all_ok = True
    for sid in ids:
        snapshot_dir = snapshots_dir / sid
        if not snapshot_dir.is_dir():
            print(f"✗ Snapshot not found: {snapshot_dir}", file=sys.stderr)
            all_ok = False
            continue
        all_ok = _run_one(
            snapshot_dir,
            check_secrets_enabled=not args.no_secrets_check,
            strict_secrets=args.strict_secrets,
        ) and all_ok

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
