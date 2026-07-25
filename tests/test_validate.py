"""Tests for hsb-validate / hsb-verify: invalid YAML, altered hash, mismatch."""
from __future__ import annotations

import json
from pathlib import Path

from hermes_skills_backup.checks import has_errors, validate_snapshot, verify_snapshot
from hermes_skills_backup.common import MANIFEST_FILENAME, read_manifest, write_manifest
from hermes_skills_backup.snapshot import create_snapshot


def test_valid_snapshot_passes_validate(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")
    manifest, issues = validate_snapshot(snapshot_dir)
    assert manifest is not None
    assert not has_errors(issues)


def test_valid_snapshot_passes_verify(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")
    manifest, issues = verify_snapshot(snapshot_dir)
    assert manifest is not None
    assert not has_errors(issues)


def test_invalid_yaml_frontmatter_flagged(hermes_home_with_bad_yaml: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home_with_bad_yaml, tmp_path / "snapshots", check_secrets=False)
    manifest, issues = validate_snapshot(snapshot_dir)
    assert manifest is not None
    assert has_errors(issues)
    assert any(i.category == "frontmatter" for i in issues)


def test_missing_required_field_flagged(hermes_home_missing_description: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home_missing_description, tmp_path / "snapshots", check_secrets=False)
    manifest, issues = validate_snapshot(snapshot_dir)
    assert has_errors(issues)
    assert any(i.category == "frontmatter" and "description" in i.message for i in issues)


def test_no_frontmatter_flagged(hermes_home_no_frontmatter: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home_no_frontmatter, tmp_path / "snapshots", check_secrets=False)
    manifest, issues = validate_snapshot(snapshot_dir)
    assert has_errors(issues)
    assert any(i.category == "frontmatter" for i in issues)


def test_altered_hash_detected_by_verify(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")

    skill_file = snapshot_dir / "profiles" / "default" / "skills" / "category-a" / "skill-alpha" / "SKILL.md"
    skill_file.write_text(skill_file.read_text() + "\ntampered content\n")

    manifest, issues = verify_snapshot(snapshot_dir)
    assert has_errors(issues)
    assert any(i.category == "hash_mismatch" for i in issues)


def test_manifest_disk_mismatch_extra_file(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")

    extra = snapshot_dir / "profiles" / "default" / "skills" / "category-a" / "skill-alpha" / "not_in_manifest.txt"
    extra.write_text("surprise\n")

    manifest, issues = verify_snapshot(snapshot_dir)
    assert has_errors(issues)
    assert any(i.category == "extra_file" for i in issues)


def test_manifest_disk_mismatch_missing_file(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")

    victim = snapshot_dir / "profiles" / "default" / "skills" / "category-a" / "skill-beta" / "SKILL.md"
    victim.unlink()

    manifest, issues = verify_snapshot(snapshot_dir)
    assert has_errors(issues)
    assert any(i.category == "missing_file" for i in issues)


def test_bad_snapshot_id_in_manifest_flagged(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")

    manifest = read_manifest(snapshot_dir / MANIFEST_FILENAME)
    manifest["snapshot_id"] = "not-a-valid-id"
    write_manifest(manifest, snapshot_dir / MANIFEST_FILENAME)

    _, issues = verify_snapshot(snapshot_dir)
    assert has_errors(issues)
    assert any(i.category in ("schema", "snapshot_id") for i in issues)


def test_corrupt_json_manifest_flagged(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")
    (snapshot_dir / MANIFEST_FILENAME).write_text("{not valid json")

    manifest, issues = verify_snapshot(snapshot_dir)
    assert manifest is None
    assert has_errors(issues)


def test_secret_in_snapshot_flagged_as_warning_by_default(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")

    leaky = snapshot_dir / "profiles" / "default" / "skills" / "category-a" / "skill-alpha" / "leaked.md"
    leaky.write_text("api_key = sk-FAKEKEYFORTESTING1234567890ABCD\n")
    # keep manifest consistent for this file-content check by adding the entry
    manifest = read_manifest(snapshot_dir / MANIFEST_FILENAME)
    from hermes_skills_backup.common import file_sha256
    rel = "category-a/skill-alpha/leaked.md"
    manifest["profiles"]["default"]["files"][rel] = {
        "sha256": file_sha256(leaky), "size_bytes": leaky.stat().st_size,
    }
    manifest["profiles"]["default"]["file_count"] = len(manifest["profiles"]["default"]["files"])
    write_manifest(manifest, snapshot_dir / MANIFEST_FILENAME)

    # Default policy: likely-secret hits are visible but non-blocking, since
    # skill docs legitimately contain token-shaped placeholder examples.
    _, issues = validate_snapshot(snapshot_dir, check_secrets_enabled=True)
    secret_issues = [i for i in issues if i.category == "secret"]
    assert secret_issues
    assert all(i.severity == "warning" for i in secret_issues)
    assert not has_errors(issues)

    # A leaked *value* is never surfaced, only path + category.
    for i in secret_issues:
        assert "sk-FAKEKEYFORTESTING1234567890ABCD" not in i.message
        assert "sk-FAKEKEYFORTESTING1234567890ABCD" not in i.path


def test_strict_secrets_promotes_hits_to_blocking_errors(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots", check_secrets=False)

    leaky = snapshot_dir / "profiles" / "default" / "skills" / "category-a" / "skill-alpha" / "leaked.md"
    leaky.write_text("api_key = sk-FAKEKEYFORTESTING1234567890ABCD\n")
    from hermes_skills_backup.common import file_sha256
    manifest = read_manifest(snapshot_dir / MANIFEST_FILENAME)
    rel = "category-a/skill-alpha/leaked.md"
    manifest["profiles"]["default"]["files"][rel] = {
        "sha256": file_sha256(leaky), "size_bytes": leaky.stat().st_size,
    }
    manifest["profiles"]["default"]["file_count"] = len(manifest["profiles"]["default"]["files"])
    write_manifest(manifest, snapshot_dir / MANIFEST_FILENAME)

    # Default: warning only, does not fail validation.
    _, default_issues = validate_snapshot(snapshot_dir, check_secrets_enabled=True, strict_secrets=False)
    assert not has_errors(default_issues)
    assert any(i.category == "secret" and i.severity == "warning" for i in default_issues)

    # --strict-secrets: the same hit becomes a blocking error.
    _, strict_issues = validate_snapshot(snapshot_dir, check_secrets_enabled=True, strict_secrets=True)
    assert has_errors(strict_issues)
    assert any(i.category == "secret" and i.severity == "error" for i in strict_issues)


def test_forbidden_state_filename_flagged(hermes_home: Path, tmp_path: Path) -> None:
    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")

    bad = snapshot_dir / "profiles" / "default" / "skills" / "config.yaml"
    bad.write_text("secret_state: true\n")
    manifest = read_manifest(snapshot_dir / MANIFEST_FILENAME)
    manifest["profiles"]["default"]["files"]["config.yaml"] = {
        "sha256": "0" * 64, "size_bytes": bad.stat().st_size,
    }
    manifest["profiles"]["default"]["file_count"] = len(manifest["profiles"]["default"]["files"])
    write_manifest(manifest, snapshot_dir / MANIFEST_FILENAME)

    _, issues = validate_snapshot(snapshot_dir, check_secrets_enabled=False)
    assert has_errors(issues)
    assert any(i.category == "forbidden_state" for i in issues)
