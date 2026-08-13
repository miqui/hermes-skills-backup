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


def test_skills_corpus_json_created_and_d3_compatible(hermes_home: Path, tmp_path: Path) -> None:
    """
    create_snapshot() must emit exactly <snapshot>/skills-corpus.json — a
    D3-compatible corpus document (see d3-hermes-skill-corpus's
    generate-corpus.mjs / src/types.ts SkillCorpus/SkillRecord shape) whose
    records are derived from the *copied* default-profile skill files inside
    this same snapshot, not from a later re-read of the live source tree.
    """
    out = tmp_path / "snapshots"
    snapshot_dir = create_snapshot(hermes_home, out)

    corpus_path = snapshot_dir / "skills-corpus.json"
    assert corpus_path.is_file()

    import json
    corpus = json.loads(corpus_path.read_text())

    # Top-level SkillCorpus shape.
    assert set(corpus) == {"generatedAt", "sourceRoot", "stats", "skills", "tree"}
    assert isinstance(corpus["generatedAt"], str) and corpus["generatedAt"]
    assert isinstance(corpus["sourceRoot"], str) and corpus["sourceRoot"]
    assert corpus["stats"]["skillCount"] == len(corpus["skills"])
    assert corpus["stats"]["nodeCount"] >= 1
    assert corpus["stats"]["maxDepth"] >= 0
    assert corpus["tree"]["type"] == "root"

    # sourceRoot must point at the snapshot's own copy, never the live
    # hermes_home fixture path — corpus data must not depend on a later
    # mutation of the original skills tree.
    assert str(hermes_home) not in corpus["sourceRoot"]
    assert "profiles/default/skills" in corpus["sourceRoot"].replace("\\", "/")

    # Records derive from the copied default-profile skill file, with the
    # SkillRecord fields the D3 app's types/UI actually consume.
    ids = {s["id"] for s in corpus["skills"]}
    assert "category-a/skill-alpha" in ids
    assert "category-a/skill-beta" in ids

    alpha = next(s for s in corpus["skills"] if s["id"] == "category-a/skill-alpha")
    for field in (
        "id", "slug", "name", "folderName", "categoryPath", "path", "skillFile",
        "description", "author", "version", "tags", "relatedSkills", "summary",
        "modifiedAt",
    ):
        assert field in alpha
    assert alpha["slug"] == "skill-alpha"
    assert alpha["folderName"] == "skill-alpha"
    assert alpha["categoryPath"] == ["category-a"]
    assert alpha["skillFile"] == "category-a/skill-alpha/SKILL.md"
    assert alpha["name"] == "skill-alpha"
    assert alpha["description"] == "skill-alpha description"

    # Acme (non-default profile) skills are out of scope for this artifact.
    assert not any(s["id"].startswith("category-b") for s in corpus["skills"])


def test_skills_corpus_tampering_detected_by_verify(hermes_home: Path, tmp_path: Path) -> None:
    """A corpus artifact edited after snapshot creation must fail hash verification."""
    from hermes_skills_backup.checks import has_errors, verify_snapshot

    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")
    corpus_path = snapshot_dir / "skills-corpus.json"
    corpus_path.write_text(corpus_path.read_text() + "\n// tampered\n")

    manifest, issues = verify_snapshot(snapshot_dir)
    assert has_errors(issues)
    assert any(i.category == "hash_mismatch" and "skills-corpus.json" in i.path for i in issues)


def test_skills_corpus_missing_artifact_detected_by_verify(hermes_home: Path, tmp_path: Path) -> None:
    """A snapshot whose manifest lists skills-corpus.json but the file was deleted must fail verify."""
    from hermes_skills_backup.checks import has_errors, verify_snapshot

    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")
    (snapshot_dir / "skills-corpus.json").unlink()

    manifest, issues = verify_snapshot(snapshot_dir)
    assert has_errors(issues)
    assert any(i.category == "missing_file" and "skills-corpus.json" in i.path for i in issues)


def test_skills_corpus_extra_untracked_artifact_detected_by_verify(hermes_home: Path, tmp_path: Path) -> None:
    """A skills-corpus.json present on disk but stripped from the manifest must not be silently exempted."""
    from hermes_skills_backup.checks import has_errors, verify_snapshot
    from hermes_skills_backup.common import write_manifest

    snapshot_dir = create_snapshot(hermes_home, tmp_path / "snapshots")
    manifest = read_manifest(snapshot_dir / MANIFEST_FILENAME)
    manifest["root_artifacts"].pop("skills-corpus.json", None)
    write_manifest(manifest, snapshot_dir / MANIFEST_FILENAME)

    _, issues = verify_snapshot(snapshot_dir)
    assert has_errors(issues)
    assert any(i.category == "extra_file" and "skills-corpus.json" in i.path for i in issues)


def test_skills_corpus_empty_default_profile_produces_valid_empty_corpus(tmp_path: Path) -> None:
    """A default profile with a skills/ dir but zero SKILL.md files still gets a well-formed, empty corpus."""
    home = tmp_path / "hermes_home_empty_default"
    (home / "skills").mkdir(parents=True)
    (home / "skills" / "README.txt").write_text("no skills here yet\n")

    snapshot_dir = create_snapshot(home, tmp_path / "snapshots", check_secrets=False)

    import json
    corpus = json.loads((snapshot_dir / "skills-corpus.json").read_text())
    assert corpus["skills"] == []
    assert corpus["stats"]["skillCount"] == 0
    assert corpus["stats"]["nodeCount"] == 1  # root only
    assert corpus["tree"]["type"] == "root"
    assert corpus["tree"]["children"] == []
