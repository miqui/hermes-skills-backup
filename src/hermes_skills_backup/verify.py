"""
hsb-verify — verify manifest integrity of a snapshot: schema/types,
snapshot id, SHA-256 of every backed-up file, exact manifest/on-disk
correspondence (no missing or unlisted files), and profiles/default
presence. Does not check YAML frontmatter content, secrets, or forbidden
state — that is hsb-validate's job (which runs these same checks too).

Usage
-----
    hsb-verify --snapshots-dir snapshots --snapshot-id <snapshot-id>
    hsb-verify --snapshots-dir snapshots --all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hermes_skills_backup.checks import has_errors, verify_snapshot
from hermes_skills_backup.common import list_snapshot_ids


def _run_one(snapshot_dir: Path) -> bool:
    manifest, issues = verify_snapshot(snapshot_dir)
    ok = manifest is not None and not has_errors(issues)

    print(f"Snapshot: {snapshot_dir.name}")
    if manifest is not None:
        file_total = sum(p.get("file_count", 0) for p in manifest.get("profiles", {}).values() if isinstance(p, dict))
        print(f"  profiles : {len(manifest.get('profiles', {}))}")
        print(f"  files    : {file_total}")

    for issue in issues:
        stream = sys.stderr if issue.severity == "error" else sys.stdout
        print(f"  {issue}", file=stream)

    print(f"  result   : {'OK' if ok else 'FAILED'} ({len(issues)} issue(s))")
    print()
    return ok


def main(argv: "list[str]" = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hsb-verify",
        description="Verify manifest/hash integrity of one or more snapshots.",
    )
    parser.add_argument("--snapshots-dir", type=Path, default=Path("snapshots"), metavar="DIR")
    parser.add_argument("--snapshot-id", default=None, metavar="ID")
    parser.add_argument("--all", action="store_true", default=False, help="Verify every snapshot in --snapshots-dir")

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
        all_ok = _run_one(snapshot_dir) and all_ok

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
