"""Tests for concise, idempotent snapshot-delta PR reporting."""
from __future__ import annotations

import shutil
from pathlib import Path

from hermes_skills_backup.pr_delta import (
    COMMENT_MARKER,
    build_delta_comment,
    upsert_pull_request_comment,
)
from hermes_skills_backup.snapshot import create_snapshot


def _write_skill(root: Path, category: str, name: str, body: str = "Test content.") -> Path:
    skill_dir = root / category / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {name} description\n---\n\n# {name}\n\n{body}\n"
    )
    return skill_dir


def _snapshot_pair(hermes_home: Path, tmp_path: Path) -> tuple[Path, Path, Path]:
    snapshots_dir = tmp_path / "snapshots"
    base = create_snapshot(hermes_home, snapshots_dir, snapshot_id="20260726T000000Z-11111111")

    default_skills = hermes_home / "skills"
    (default_skills / "category-a" / "skill-alpha" / "references" / "notes.md").write_text("changed notes\n")
    shutil.rmtree(default_skills / "category-a" / "skill-beta")
    _write_skill(default_skills, "category-a", "skill-new")

    current = create_snapshot(hermes_home, snapshots_dir, snapshot_id="20260726T010000Z-22222222")
    return snapshots_dir, base, current


def test_delta_comment_lists_only_changed_skills(hermes_home: Path, tmp_path: Path) -> None:
    snapshots_dir, _base, current = _snapshot_pair(hermes_home, tmp_path)

    comment = build_delta_comment(snapshots_dir, [current.name])

    assert COMMENT_MARKER in comment
    assert f"`{current.name}`" in comment
    assert "New skills (1)" in comment
    assert "Modified skills (1)" in comment
    assert "Removed skills (1)" in comment
    assert "`default/category-a/skill-new`" in comment
    assert "`default/category-a/skill-alpha`" in comment
    assert "`default/category-a/skill-beta`" in comment
    assert "skill-gamma" not in comment


def test_delta_comment_is_idempotently_updated_when_marker_exists() -> None:
    calls: list[tuple[str, str, object | None]] = []

    def request_json(method: str, url: str, token: str, payload: object | None = None) -> object:
        calls.append((method, url, payload))
        if method == "GET":
            return [{"id": 42, "body": f"old\n{COMMENT_MARKER}"}]
        assert method == "PATCH"
        return {"id": 42}

    result = upsert_pull_request_comment(
        api_base="https://api.github.example",
        repository="owner/repo",
        pull_request_number=9,
        token="test-token",
        body=f"new\n{COMMENT_MARKER}",
        request_json=request_json,
    )

    assert result == "updated"
    assert calls == [
        ("GET", "https://api.github.example/repos/owner/repo/issues/9/comments?per_page=100", None),
        (
            "PATCH",
            "https://api.github.example/repos/owner/repo/issues/comments/42",
            {"body": f"new\n{COMMENT_MARKER}"},
        ),
    ]


def test_delta_comment_is_created_when_marker_is_absent() -> None:
    calls: list[tuple[str, str, object | None]] = []

    def request_json(method: str, url: str, token: str, payload: object | None = None) -> object:
        calls.append((method, url, payload))
        if method == "GET":
            return []
        assert method == "POST"
        return {"id": 43}

    result = upsert_pull_request_comment(
        api_base="https://api.github.example",
        repository="owner/repo",
        pull_request_number=9,
        token="test-token",
        body=f"new\n{COMMENT_MARKER}",
        request_json=request_json,
    )

    assert result == "created"
    assert calls == [
        ("GET", "https://api.github.example/repos/owner/repo/issues/9/comments?per_page=100", None),
        (
            "POST",
            "https://api.github.example/repos/owner/repo/issues/9/comments",
            {"body": f"new\n{COMMENT_MARKER}"},
        ),
    ]
