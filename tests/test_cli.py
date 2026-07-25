"""End-to-end tests for the hsb-* console entry points (main() functions)."""
from __future__ import annotations

from pathlib import Path

from hermes_skills_backup import restore as restore_mod
from hermes_skills_backup import snapshot as snapshot_mod
from hermes_skills_backup import validate as validate_mod
from hermes_skills_backup import verify as verify_mod


def test_snapshot_then_validate_then_verify_cli(hermes_home: Path, tmp_path: Path) -> None:
    out = tmp_path / "snapshots"
    rc = snapshot_mod.main([
        "--hermes-home", str(hermes_home),
        "--output-dir", str(out),
        "--snapshot-id", "20260725T000000Z-cafe0001",
    ])
    assert rc == 0
    assert (out / "20260725T000000Z-cafe0001" / "MANIFEST.json").is_file()

    rc = validate_mod.main([
        "--snapshots-dir", str(out),
        "--snapshot-id", "20260725T000000Z-cafe0001",
    ])
    assert rc == 0

    rc = verify_mod.main([
        "--snapshots-dir", str(out),
        "--all",
    ])
    assert rc == 0


def test_validate_all_flag(hermes_home: Path, tmp_path: Path) -> None:
    out = tmp_path / "snapshots"
    snapshot_mod.main(["--hermes-home", str(hermes_home), "--output-dir", str(out), "--snapshot-id", "20260725T000000Z-aaaaaaaa"])
    rc = validate_mod.main(["--snapshots-dir", str(out), "--all"])
    assert rc == 0


def test_validate_requires_id_or_all(tmp_path: Path) -> None:
    out = tmp_path / "snapshots"
    out.mkdir()
    import pytest
    with pytest.raises(SystemExit) as exc_info:
        validate_mod.main(["--snapshots-dir", str(out)])
    assert exc_info.value.code == 2


def test_restore_cli_dry_run_then_apply(hermes_home: Path, tmp_path: Path) -> None:
    out = tmp_path / "snapshots"
    snapshot_mod.main(["--hermes-home", str(hermes_home), "--output-dir", str(out), "--snapshot-id", "20260725T000000Z-1a2b3c4d"])

    target = tmp_path / "target_home"
    rc = restore_mod.main([
        "--snapshots-dir", str(out),
        "--snapshot-id", "20260725T000000Z-1a2b3c4d",
        "--target-hermes-home", str(target),
    ])
    assert rc == 0
    assert not target.exists()

    rc = restore_mod.main([
        "--snapshots-dir", str(out),
        "--snapshot-id", "20260725T000000Z-1a2b3c4d",
        "--target-hermes-home", str(target),
        "--apply",
    ])
    assert rc == 0
    assert (target / "skills" / "category-a" / "skill-alpha" / "SKILL.md").is_file()
    assert (target / "profiles" / "acme" / "skills" / "category-b" / "skill-gamma" / "SKILL.md").is_file()


def test_restore_cli_missing_snapshot(tmp_path: Path) -> None:
    out = tmp_path / "snapshots"
    out.mkdir()
    rc = restore_mod.main([
        "--snapshots-dir", str(out),
        "--snapshot-id", "does-not-exist",
        "--target-hermes-home", str(tmp_path / "target"),
    ])
    assert rc == 1
