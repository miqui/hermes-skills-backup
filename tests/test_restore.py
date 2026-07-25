"""Tests for hsb-restore: dry-run, apply, traversal/symlink safety."""
from __future__ import annotations

from pathlib import Path

import pytest

from hermes_skills_backup.common import (
    MANIFEST_FILENAME,
    PathSafetyError,
    is_dangerous_target,
    read_manifest,
    safe_relpath_join,
    write_manifest,
)
from hermes_skills_backup.restore import RestoreAborted, restore_snapshot
from hermes_skills_backup.snapshot import create_snapshot


def test_dry_run_restore_makes_no_changes(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")
    target = tmp_path / "restore_target" / "hermes_home"

    report = restore_snapshot(snapshot_dir, target, apply=False)

    assert report["applied"] is False
    assert not target.exists()
    names = {p["name"] for p in report["profiles"]}
    assert names == {"default", "acme"}


def test_applied_restore_writes_files(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")
    target = tmp_path / "restore_target" / "hermes_home"

    report = restore_snapshot(snapshot_dir, target, apply=True)

    assert report["applied"] is True
    assert (target / "skills" / "category-a" / "skill-alpha" / "SKILL.md").is_file()
    assert (target / "profiles" / "acme" / "skills" / "category-b" / "skill-gamma" / "SKILL.md").is_file()

    original = (
        hermes_home / "skills" / "category-a" / "skill-alpha" / "SKILL.md"
    ).read_text()
    restored = (
        target / "skills" / "category-a" / "skill-alpha" / "SKILL.md"
    ).read_text()
    assert original == restored

    # excluded entries never appear in restored target
    assert not (target / "skills" / ".curator_backups").exists()
    assert not (target / "skills" / ".hub").exists()


def test_applied_restore_preserves_profile_layout(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")
    target = tmp_path / "restore_target2" / "hermes_home"
    restore_snapshot(snapshot_dir, target, apply=True)

    assert (target / "skills").is_dir()
    assert (target / "profiles" / "acme" / "skills").is_dir()
    assert not (target / "profiles" / "default").exists()


def test_restore_replaces_existing_destination(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")
    target = tmp_path / "restore_target3" / "hermes_home"

    (target / "skills" / "stale-category" / "stale-skill").mkdir(parents=True)
    (target / "skills" / "stale-category" / "stale-skill" / "SKILL.md").write_text("stale\n")

    report = restore_snapshot(snapshot_dir, target, apply=True)
    default_entry = next(p for p in report["profiles"] if p["name"] == "default")
    assert default_entry["would_replace_existing"] is True
    assert not (target / "skills" / "stale-category").exists()
    assert (target / "skills" / "category-a" / "skill-alpha" / "SKILL.md").is_file()


def test_restore_refuses_dangerous_targets(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")

    with pytest.raises(RestoreAborted):
        restore_snapshot(snapshot_dir, Path("/"), apply=False)

    with pytest.raises(RestoreAborted):
        restore_snapshot(snapshot_dir, Path.home(), apply=False)


def test_restore_aborts_on_tampered_snapshot(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")
    skill_file = snapshot_dir / "profiles" / "default" / "skills" / "category-a" / "skill-alpha" / "SKILL.md"
    skill_file.write_text(skill_file.read_text() + "\ntampered\n")

    target = tmp_path / "restore_target4" / "hermes_home"
    with pytest.raises(RestoreAborted):
        restore_snapshot(snapshot_dir, target, apply=True)
    assert not target.exists()


def test_restore_aborts_on_manifest_traversal_entry(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")
    manifest = read_manifest(snapshot_dir / MANIFEST_FILENAME)
    manifest["profiles"]["default"]["files"]["../../etc/passwd"] = {
        "sha256": "0" * 64, "size_bytes": 0,
    }
    manifest["profiles"]["default"]["file_count"] = len(manifest["profiles"]["default"]["files"])
    write_manifest(manifest, snapshot_dir / MANIFEST_FILENAME)

    target = tmp_path / "restore_target5" / "hermes_home"
    with pytest.raises(RestoreAborted):
        restore_snapshot(snapshot_dir, target, apply=True)
    assert not target.exists()


def test_safe_relpath_join_rejects_traversal(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    for bad in ("../escape", "a/../../escape", "/etc/passwd", "..", "."):
        with pytest.raises(PathSafetyError):
            safe_relpath_join(base, bad)


def test_safe_relpath_join_rejects_symlink_escape(tmp_path: Path) -> None:
    base = tmp_path / "base"
    base.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = base / "link_out"
    link.symlink_to(outside, target_is_directory=True)

    # a path that traverses through a symlinked directory resolves outside
    # base and must be rejected, even though it is lexically clean
    with pytest.raises(PathSafetyError):
        safe_relpath_join(base, "link_out/file.txt")


def test_is_dangerous_target_rejects_symlink(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link = tmp_path / "link_to_real"
    link.symlink_to(real_dir, target_is_directory=True)
    assert is_dangerous_target(link) is not None


def test_is_dangerous_target_accepts_reasonable_target(tmp_path: Path) -> None:
    target = tmp_path / "some" / "nested" / "hermes_home"
    assert is_dangerous_target(target) is None
