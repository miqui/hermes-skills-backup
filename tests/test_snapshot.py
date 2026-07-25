"""Tests for hsb-snapshot: multi-profile capture, exclusions, secrets, symlinks."""
from __future__ import annotations

from pathlib import Path

import pytest

from hermes_skills_backup.common import (
    MANIFEST_FILENAME,
    RESTORE_FILENAME,
    SecretsDetected,
    read_manifest,
)
from hermes_skills_backup.snapshot import create_snapshot


def test_multi_profile_capture(hermes_home: Path, tmp_path: Path) -> None:
    """default + a secondary named profile are both captured with correct layout."""
    out = tmp_path / "snapshots"
    snapshot_dir = create_snapshot(hermes_home, out)

    manifest = read_manifest(snapshot_dir / MANIFEST_FILENAME)
    profiles = manifest["profiles"]

    assert set(profiles) == {"default", "acme"}
    assert profiles["default"]["skills_path"] == "profiles/default/skills"
    assert profiles["acme"]["skills_path"] == "profiles/acme/skills"

    assert (snapshot_dir / "profiles" / "default" / "skills").is_dir()
    assert (snapshot_dir / "profiles" / "acme" / "skills").is_dir()
    assert (snapshot_dir / MANIFEST_FILENAME).is_file()
    assert (snapshot_dir / RESTORE_FILENAME).is_file()

    # skill content actually copied
    assert (snapshot_dir / "profiles" / "default" / "skills" / "category-a" / "skill-alpha" / "SKILL.md").is_file()
    assert (snapshot_dir / "profiles" / "acme" / "skills" / "category-b" / "skill-gamma" / "SKILL.md").is_file()

    # nested hidden asset preserved
    assert (
        snapshot_dir / "profiles" / "default" / "skills" / "category-a" / "skill-alpha" / ".gitkeep"
    ).is_file()


def test_exclusions_top_level_hidden_entries(hermes_home: Path, tmp_path: Path) -> None:
    """.curator_backups, .hub, and other top-level dotfiles are excluded."""
    out = tmp_path / "snapshots"
    snapshot_dir = create_snapshot(hermes_home, out)

    default_root = snapshot_dir / "profiles" / "default" / "skills"
    assert not (default_root / ".curator_backups").exists()
    assert not (default_root / ".hub").exists()
    assert not (default_root / ".usage.json").exists()

    manifest = read_manifest(snapshot_dir / MANIFEST_FILENAME)
    for rel in manifest["profiles"]["default"]["files"]:
        assert ".curator_backups" not in rel
        assert ".hub" not in rel
        assert rel != ".usage.json"


def test_manifest_hashes_every_file(hermes_home: Path, tmp_path: Path) -> None:
    out = tmp_path / "snapshots"
    snapshot_dir = create_snapshot(hermes_home, out)
    manifest = read_manifest(snapshot_dir / MANIFEST_FILENAME)

    for name, entry in manifest["profiles"].items():
        skills_root = snapshot_dir / "profiles" / name / "skills"
        on_disk = {
            p.relative_to(skills_root).as_posix()
            for p in skills_root.rglob("*")
            if p.is_file()
        }
        assert set(entry["files"]) == on_disk
        assert entry["file_count"] == len(on_disk)
        for meta in entry["files"].values():
            assert len(meta["sha256"]) == 64
            assert isinstance(meta["size_bytes"], int)


def test_manifest_has_no_source_paths_or_host_data(hermes_home: Path, tmp_path: Path) -> None:
    out = tmp_path / "snapshots"
    snapshot_dir = create_snapshot(hermes_home, out)
    raw = (snapshot_dir / MANIFEST_FILENAME).read_text()

    assert str(hermes_home) not in raw
    assert str(tmp_path) not in raw
    import socket
    hostname = socket.gethostname()
    if hostname:
        assert hostname not in raw
    import getpass
    assert getpass.getuser() not in raw


def test_empty_profile_directory_excluded(hermes_home_empty_profile: Path, tmp_path: Path) -> None:
    out = tmp_path / "snapshots"
    snapshot_dir = create_snapshot(hermes_home_empty_profile, out)
    manifest = read_manifest(snapshot_dir / MANIFEST_FILENAME)
    assert set(manifest["profiles"]) == {"default"}


def test_secrets_detected_aborts_snapshot(hermes_home_with_secret: Path, tmp_path: Path) -> None:
    out = tmp_path / "snapshots"
    with pytest.raises(SecretsDetected):
        create_snapshot(hermes_home_with_secret, out, check_secrets=True)
    assert not out.exists() or not any(out.iterdir())


def test_symlinks_never_followed_or_included(hermes_home_with_symlink, tmp_path: Path) -> None:
    home, outside = hermes_home_with_symlink
    out = tmp_path / "snapshots"
    snapshot_dir = create_snapshot(home, out)

    manifest = read_manifest(snapshot_dir / MANIFEST_FILENAME)
    for rel in manifest["profiles"]["default"]["files"]:
        assert "escape-link" not in rel
        assert "secret.txt" not in rel

    for p in (snapshot_dir / "profiles" / "default" / "skills").rglob("*"):
        assert not p.is_symlink()
        assert "outside_secret" not in str(p)


def test_snapshot_already_exists_raises(hermes_home: Path, tmp_path: Path) -> None:
    out = tmp_path / "snapshots"
    snapshot_dir = create_snapshot(hermes_home, out, snapshot_id="fixed-id-0001")
    assert snapshot_dir.name == "fixed-id-0001"
    with pytest.raises(FileExistsError):
        create_snapshot(hermes_home, out, snapshot_id="fixed-id-0001")


def test_no_profiles_raises(tmp_path: Path) -> None:
    empty_home = tmp_path / "no_skills_here"
    empty_home.mkdir()
    out = tmp_path / "snapshots"
    with pytest.raises(RuntimeError):
        create_snapshot(empty_home, out)
