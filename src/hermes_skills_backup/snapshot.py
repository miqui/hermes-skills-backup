"""
hsb-snapshot — create a portable snapshot of every Hermes skill profile.

Layout produced
----------------
    <output-dir>/<snapshot-id>/
        MANIFEST.json
        RESTORE.md
        profiles/
            default/skills/         copied from <hermes-home>/skills
            <profile-name>/skills/  copied from <hermes-home>/profiles/<profile-name>/skills

Only profiles with a skills directory are included. Hidden/internal
top-level entries (.curator_backups, .hub, and other Hermes runtime
bookkeeping) are excluded; nested skill assets — including legitimately
hidden ones — are preserved. No config, auth, session, cache, log, or other
out-of-scope Hermes state is ever touched, since only skills/ trees are read.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from hermes_skills_backup.common import (
    SecretsDetected,
    compute_profile_files,
    default_hermes_home,
    discover_profiles,
    file_sha256,
    find_symlinks,
    iter_included_files,
    new_snapshot_id,
    read_manifest,
    scan_tree_for_secrets,
    snapshot_profile_skills_dir,
    utc_now_iso,
    write_manifest,
    write_restore_md,
    assemble_manifest,
    CORPUS_FILENAME,
    DEFAULT_PROFILE,
    MANIFEST_FILENAME,
    PROFILES_DIRNAME,
    RESTORE_FILENAME,
)
from hermes_skills_backup.corpus import build_corpus


def create_snapshot(
    hermes_home: Path,
    output_dir: Path,
    snapshot_id: str = None,
    check_secrets: bool = True,
) -> Path:
    """
    Build a snapshot directory under *output_dir* and return its path.
    Raises SecretsDetected (with no snapshot written) if the secrets scan
    fires and check_secrets=True. Raises RuntimeError if no profile has a
    skills directory.
    """
    if not hermes_home.is_dir():
        raise FileNotFoundError(f"Hermes home not found: {hermes_home}")

    profiles = discover_profiles(hermes_home)
    if not profiles:
        raise RuntimeError(f"No profile skills directories found under {hermes_home} — nothing to snapshot.")

    per_profile_files: "dict[str, list[Path]]" = {
        name: list(iter_included_files(root)) for name, root in profiles.items()
    }

    if check_secrets:
        offenders = []
        for files in per_profile_files.values():
            offenders += scan_tree_for_secrets(files)
        if offenders:
            raise SecretsDetected(offenders)

    for root in profiles.values():
        for symlink in find_symlinks(root):
            print(f"  ! skipping symlink (not included): {symlink}", file=sys.stderr)

    snapshot_id = snapshot_id or new_snapshot_id()
    snapshot_dir = output_dir / snapshot_id
    if snapshot_dir.exists():
        raise FileExistsError(f"Snapshot directory already exists: {snapshot_dir}")

    profile_manifest_files: "dict[str, dict]" = {}
    staging_root = output_dir / f".{snapshot_id}.staging"
    if staging_root.exists():
        shutil.rmtree(staging_root)

    try:
        for name, root in profiles.items():
            dest = snapshot_profile_skills_dir(staging_root, name)
            dest.mkdir(parents=True, exist_ok=True)
            for f in per_profile_files[name]:
                rel = f.relative_to(root)
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)
            profile_manifest_files[name] = compute_profile_files(root)

        # Build the D3 skills-corpus.json artifact from the *staged copy* of
        # the default profile — never the live source — so the corpus can
        # never drift from what this snapshot actually contains, and a later
        # mutation of the live skills tree can never change it retroactively.
        root_artifacts: "dict[str, dict]" = {}
        if DEFAULT_PROFILE in profiles:
            default_staged_dir = snapshot_profile_skills_dir(staging_root, DEFAULT_PROFILE)
            source_root_label = f"{PROFILES_DIRNAME}/{DEFAULT_PROFILE}/skills"
            corpus = build_corpus(default_staged_dir, source_root_label, utc_now_iso())
            corpus_path = staging_root / CORPUS_FILENAME
            corpus_path.write_text(json.dumps(corpus, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
            root_artifacts[CORPUS_FILENAME] = {
                "sha256": file_sha256(corpus_path),
                "size_bytes": corpus_path.stat().st_size,
            }

        manifest = assemble_manifest(profile_manifest_files, snapshot_id, utc_now_iso(), root_artifacts)
        write_manifest(manifest, staging_root / MANIFEST_FILENAME)
        write_restore_md(manifest, staging_root / RESTORE_FILENAME)

        output_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staging_root), str(snapshot_dir))
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root, ignore_errors=True)

    return snapshot_dir


def main(argv: "list[str]" = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hsb-snapshot",
        description="Create a portable snapshot of every Hermes skill profile.",
    )
    parser.add_argument(
        "--hermes-home", type=Path, default=default_hermes_home(), metavar="DIR",
        help="Hermes home directory to back up (default: ~/.hermes)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("snapshots"), metavar="DIR",
        help="Directory in which to create the snapshot (default: ./snapshots)",
    )
    parser.add_argument(
        "--snapshot-id", default=None,
        help="Override the auto-generated snapshot id",
    )
    parser.add_argument(
        "--no-secrets-check", action="store_true", default=False,
        help="Skip the secrets scan (not recommended)",
    )

    args = parser.parse_args(argv)

    try:
        hermes_home = args.hermes_home.expanduser().resolve()
        output_dir = args.output_dir.expanduser().resolve()
        snapshot_dir = create_snapshot(
            hermes_home=hermes_home,
            output_dir=output_dir,
            snapshot_id=args.snapshot_id,
            check_secrets=not args.no_secrets_check,
        )
    except SecretsDetected as exc:
        print(f"✗ ABORTED — {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"✗ Error: {exc}", file=sys.stderr)
        return 1

    manifest = read_manifest(snapshot_dir / MANIFEST_FILENAME)
    profiles = manifest["profiles"]
    total_files = sum(p["file_count"] for p in profiles.values())
    skill_count = sum(
        1
        for p in profiles.values()
        for rel in p["files"]
        if Path(rel).name == "SKILL.md"
    )

    print(f"✓ Snapshot created: {snapshot_dir}")
    print(f"  snapshot id : {manifest['snapshot_id']}")
    print(f"  profiles    : {len(profiles)} ({', '.join(sorted(profiles))})")
    print(f"  SKILL.md    : {skill_count}")
    print(f"  total files : {total_files}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
