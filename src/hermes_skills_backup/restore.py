"""
hsb-restore — safely restore a snapshot into a target Hermes home.

Safety model
------------
* Dry-run by default; nothing is written unless --apply is passed.
* The snapshot is fully integrity-checked (schema, hashes, on-disk
  correspondence, symlink/path-escape safety) before any restore plan is
  built — a snapshot that fails verification is never restored.
* The target Hermes home is checked against a list of dangerous/ambiguous
  destinations (filesystem root, home directory, well-known system dirs,
  symlinks, too-shallow paths) and rejected if unsafe.
* Every file is staged into a temporary directory and hash-verified again
  before anything under the target is touched.
* Only the exact per-profile skills directories being restored
  (<target>/skills and <target>/profiles/<name>/skills) are ever removed —
  nothing else under the target, and nothing outside the target, is ever
  modified or deleted.

Usage
-----
    # Dry run (default — prints the plan, changes nothing):
    hsb-restore --snapshots-dir snapshots --snapshot-id <id> \\
        --target-hermes-home /path/to/target

    # Apply:
    hsb-restore --snapshots-dir snapshots --snapshot-id <id> \\
        --target-hermes-home /path/to/target --apply
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from hermes_skills_backup.checks import has_errors, verify_snapshot
from hermes_skills_backup.common import (
    PathSafetyError,
    file_sha256,
    is_dangerous_target,
    profile_source_skills_dir,
    safe_relpath_join,
    snapshot_profile_skills_dir,
)


class RestoreAborted(RuntimeError):
    pass


def restore_snapshot(
    snapshot_dir: Path,
    target_hermes_home: Path,
    apply: bool = False,
) -> "dict":
    """
    Restore every profile in *snapshot_dir* into *target_hermes_home*.
    Returns a report dict. Raises RestoreAborted on any safety violation
    or integrity failure — nothing is written in that case.
    """
    manifest, issues = verify_snapshot(snapshot_dir)
    if manifest is None or has_errors(issues):
        details = "\n".join(f"  {i}" for i in issues)
        raise RestoreAborted(f"Snapshot failed integrity verification — refusing to restore.\n{details}")

    danger = is_dangerous_target(target_hermes_home)
    if danger:
        raise RestoreAborted(f"Refusing unsafe restore target ({target_hermes_home}): {danger}")

    target_home = target_hermes_home.expanduser().resolve(strict=False)
    profiles = manifest["profiles"]

    plan = []
    for name in sorted(profiles):
        src_root = snapshot_profile_skills_dir(snapshot_dir, name)
        dest = profile_source_skills_dir(target_home, name)
        dest_resolved = dest.resolve(strict=False)
        if dest_resolved != target_home and target_home not in dest_resolved.parents:
            raise RestoreAborted(f"Computed destination escapes target home: {dest_resolved}")
        plan.append((name, src_root, dest, profiles[name]["files"]))

    report = {
        "snapshot_id": manifest["snapshot_id"],
        "target_hermes_home": str(target_home),
        "applied": False,
        "profiles": [],
    }

    with tempfile.TemporaryDirectory(prefix="hsb-restore-stage-") as tmpdir:
        stage_root = Path(tmpdir)
        staged_dirs = {}

        for name, src_root, dest, files in plan:
            staged = stage_root / name
            staged.mkdir(parents=True, exist_ok=True)
            written = 0
            for rel, meta in files.items():
                src_file = safe_relpath_join(src_root, rel)
                if not src_file.is_file() or src_file.is_symlink():
                    raise RestoreAborted(f"Snapshot source file missing or unsafe: {src_file}")
                actual_sha = file_sha256(src_file)
                if actual_sha != meta.get("sha256"):
                    raise RestoreAborted(f"Hash changed since verification: {src_file}")
                dest_file = safe_relpath_join(staged, rel)
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest_file)
                written += 1
            staged_dirs[name] = staged
            report["profiles"].append({
                "name": name,
                "destination": str(dest),
                "file_count": written,
                "would_replace_existing": dest.exists(),
            })

        if not apply:
            return report

        target_home.mkdir(parents=True, exist_ok=True)
        for name, src_root, dest, files in plan:
            staged = staged_dirs[name]
            if dest.exists():
                if dest.is_symlink():
                    raise RestoreAborted(f"Refusing to replace a symlink at destination: {dest}")
                if not dest.is_dir():
                    raise RestoreAborted(f"Destination exists and is not a directory: {dest}")
                dest_resolved = dest.resolve()
                if dest_resolved != target_home and target_home not in dest_resolved.parents:
                    raise RestoreAborted(f"Refusing to remove path outside target home: {dest_resolved}")
                shutil.rmtree(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(staged), str(dest))

    report["applied"] = True
    return report


def _print_report(report: "dict") -> None:
    mode = "APPLIED" if report["applied"] else "DRY RUN"
    print(f"[{mode}] snapshot {report['snapshot_id']} -> {report['target_hermes_home']}")
    for p in report["profiles"]:
        action = "replace" if p["would_replace_existing"] else "create"
        print(f"  profile '{p['name']}': {action} {p['destination']} ({p['file_count']} file(s))")
    if not report["applied"]:
        print("\nDry run only — no files were written. Re-run with --apply to execute.")


def main(argv: "list[str]" = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hsb-restore",
        description=(
            "Restore a snapshot into a target Hermes home. "
            "DEFAULT IS DRY-RUN — pass --apply to write files."
        ),
    )
    parser.add_argument("--snapshots-dir", type=Path, default=Path("snapshots"), metavar="DIR")
    parser.add_argument("--snapshot-id", required=True, metavar="ID")
    parser.add_argument(
        "--target-hermes-home", required=True, type=Path, metavar="DIR",
        help="Destination Hermes home to rebuild profile skills paths into",
    )
    parser.add_argument("--apply", action="store_true", default=False, help="Actually write files (default: dry-run)")

    args = parser.parse_args(argv)
    snapshots_dir = args.snapshots_dir.expanduser().resolve()
    snapshot_dir = snapshots_dir / args.snapshot_id

    if not snapshot_dir.is_dir():
        print(f"✗ Snapshot not found: {snapshot_dir}", file=sys.stderr)
        return 1

    try:
        report = restore_snapshot(
            snapshot_dir=snapshot_dir,
            target_hermes_home=args.target_hermes_home,
            apply=args.apply,
        )
    except (RestoreAborted, PathSafetyError) as exc:
        print(f"✗ Restore aborted: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"✗ Error: {exc}", file=sys.stderr)
        return 1

    _print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
