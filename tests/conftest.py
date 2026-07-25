# tests/conftest.py
"""Shared pytest fixtures for hermes-skills-backup tests."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

GOOD_SKILL_MD = textwrap.dedent("""\
    ---
    name: {name}
    description: "{description}"
    version: 1.0.0
    ---

    # {name}

    Test content.
""")

BAD_YAML_SKILL_MD = textwrap.dedent("""\
    ---
    name: broken-skill
    description: [unterminated list
    ---

    # Broken Skill
""")

MISSING_DESC_SKILL_MD = textwrap.dedent("""\
    ---
    name: no-desc-skill
    ---

    # No Description
""")

NO_FRONTMATTER_SKILL_MD = textwrap.dedent("""\
    # No Frontmatter

    This file has no leading YAML block at all.
""")


def _write_skill(base: Path, category: str, name: str, description: str = None) -> Path:
    d = base / category / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(
        GOOD_SKILL_MD.format(name=name, description=description or f"{name} description")
    )
    return d


@pytest.fixture()
def hermes_home(tmp_path: Path) -> Path:
    """
    A realistic fake Hermes home:
      - default profile (~/.hermes/skills) with two skills, one carrying
        nested support artifacts including a legitimately hidden nested
        file that must be PRESERVED (not confused with top-level exclusions)
      - a secondary named profile 'acme' (~/.hermes/profiles/acme/skills)
        with one skill
      - top-level hidden/internal entries (.curator_backups, .hub, and a
        runtime-state dotfile) directly under the default skills root that
        must be EXCLUDED from any snapshot
    """
    home = tmp_path / "hermes_home"

    default_skills = home / "skills"
    d = _write_skill(default_skills, "category-a", "skill-alpha")
    (d / "references").mkdir()
    (d / "references" / "notes.md").write_text("# notes\n")
    (d / ".gitkeep").write_text("")  # nested hidden support artifact -> preserved

    _write_skill(default_skills, "category-a", "skill-beta")

    (default_skills / ".curator_backups" / "2026-01-01").mkdir(parents=True)
    (default_skills / ".curator_backups" / "2026-01-01" / "SKILL.md").write_text("must be excluded\n")
    (default_skills / ".hub").mkdir()
    (default_skills / ".hub" / "data.json").write_text("{}")
    (default_skills / ".usage.json").write_text("{}")

    acme_skills = home / "profiles" / "acme" / "skills"
    _write_skill(acme_skills, "category-b", "skill-gamma")

    return home


@pytest.fixture()
def hermes_home_with_bad_yaml(tmp_path: Path) -> Path:
    home = tmp_path / "hermes_home_bad_yaml"
    d = home / "skills" / "cat" / "broken-skill"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(BAD_YAML_SKILL_MD)
    return home


@pytest.fixture()
def hermes_home_missing_description(tmp_path: Path) -> Path:
    home = tmp_path / "hermes_home_missing_desc"
    d = home / "skills" / "cat" / "no-desc-skill"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(MISSING_DESC_SKILL_MD)
    return home


@pytest.fixture()
def hermes_home_no_frontmatter(tmp_path: Path) -> Path:
    home = tmp_path / "hermes_home_no_frontmatter"
    d = home / "skills" / "cat" / "no-frontmatter-skill"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(NO_FRONTMATTER_SKILL_MD)
    return home


@pytest.fixture()
def hermes_home_with_secret(tmp_path: Path) -> Path:
    home = tmp_path / "hermes_home_secret"
    d = _write_skill(home / "skills", "cat", "leaky-skill")
    (d / "config.md").write_text("api_key = sk-FAKEKEYFORTESTING1234567890ABCD\n")
    return home


@pytest.fixture()
def hermes_home_with_symlink(tmp_path: Path):
    """
    A skills tree containing a symlink pointing outside the tree. Snapshot
    creation must never follow or include it.
    """
    home = tmp_path / "hermes_home_symlink"
    outside = tmp_path / "outside_secret"
    outside.mkdir()
    (outside / "secret.txt").write_text("outside content\n")

    d = _write_skill(home / "skills", "cat", "linked-skill")
    (d / "escape-link").symlink_to(outside)
    return home, outside


@pytest.fixture()
def hermes_home_empty_profile(tmp_path: Path) -> Path:
    """A named profile directory that exists but has no skills/ subdirectory
    — it must be excluded entirely from the snapshot."""
    home = tmp_path / "hermes_home_empty_profile"
    _write_skill(home / "skills", "cat", "only-default-skill")
    (home / "profiles" / "ghost").mkdir(parents=True)
    return home
