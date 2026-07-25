"""
Shared verification/validation check functions used by hsb-verify (manifest
+ hash integrity only) and hsb-validate (integrity plus content-level
checks: YAML frontmatter, secrets, forbidden state).

Every check function returns a list of Issue objects rather than raising,
so callers can aggregate a full report instead of failing on the first
problem.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from hermes_skills_backup.common import (
    DEFAULT_PROFILE,
    FORBIDDEN_STATE_DIRNAMES,
    FORBIDDEN_STATE_FILENAMES,
    MANIFEST_FILENAME,
    PathSafetyError,
    SAFE_NAME_RE,
    SCHEMA_VERSION,
    SHA256_RE,
    SNAPSHOT_ID_RE,
    file_sha256,
    parse_skill_frontmatter,
    profile_skills_rel_path,
    read_manifest,
    safe_relpath_join,
    scan_file_for_secrets,
    snapshot_profile_skills_dir,
    walk_tree,
)


@dataclass
class Issue:
    severity: str  # "error" or "warning"
    category: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.category}: {self.path}: {self.message}"


def has_errors(issues: List[Issue]) -> bool:
    return any(i.severity == "error" for i in issues)


# ---------------------------------------------------------------------------
# Manifest schema / type checks
# ---------------------------------------------------------------------------

def load_and_check_manifest_schema(
    snapshot_dir: Path,
) -> Tuple[Optional[dict], List[Issue]]:
    issues: List[Issue] = []
    manifest_path = snapshot_dir / MANIFEST_FILENAME

    if not manifest_path.is_file():
        issues.append(Issue("error", "schema", str(manifest_path), "MANIFEST.json is missing"))
        return None, issues

    try:
        manifest = read_manifest(manifest_path)
    except Exception as exc:  # noqa: BLE001
        issues.append(Issue("error", "schema", str(manifest_path), f"MANIFEST.json is not valid JSON: {exc}"))
        return None, issues

    if not isinstance(manifest, dict):
        issues.append(Issue("error", "schema", str(manifest_path), "MANIFEST.json root must be an object"))
        return None, issues

    if manifest.get("schema_version") != SCHEMA_VERSION:
        issues.append(Issue(
            "error", "schema", str(manifest_path),
            f"schema_version must be {SCHEMA_VERSION}, got {manifest.get('schema_version')!r}",
        ))

    snapshot_id = manifest.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not SNAPSHOT_ID_RE.match(snapshot_id):
        issues.append(Issue(
            "error", "schema", str(manifest_path),
            f"snapshot_id missing or malformed: {snapshot_id!r}",
        ))

    created_utc = manifest.get("created_utc")
    if not isinstance(created_utc, str):
        issues.append(Issue("error", "schema", str(manifest_path), "created_utc missing or not a string"))
    else:
        try:
            datetime.strptime(created_utc, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            issues.append(Issue("error", "schema", str(manifest_path), f"created_utc is not valid ISO-8601 UTC: {created_utc!r}"))

    generator = manifest.get("generator")
    if not isinstance(generator, dict) or not isinstance(generator.get("name"), str):
        issues.append(Issue("error", "schema", str(manifest_path), "generator must be an object with a 'name' string"))

    profiles = manifest.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        issues.append(Issue("error", "schema", str(manifest_path), "profiles must be a non-empty object"))
        return manifest, issues

    if DEFAULT_PROFILE not in profiles:
        issues.append(Issue("error", "profile", str(manifest_path), "manifest is missing the 'default' profile"))

    for name, entry in profiles.items():
        loc = f"{manifest_path}#profiles.{name}"
        if not SAFE_NAME_RE.match(name):
            issues.append(Issue("error", "schema", loc, f"unsafe profile name: {name!r}"))
        if not isinstance(entry, dict):
            issues.append(Issue("error", "schema", loc, "profile entry must be an object"))
            continue
        expected_skills_path = profile_skills_rel_path(name)
        if entry.get("skills_path") != expected_skills_path:
            issues.append(Issue(
                "error", "schema", loc,
                f"skills_path must be {expected_skills_path!r}, got {entry.get('skills_path')!r}",
            ))
        files = entry.get("files")
        if not isinstance(files, dict):
            issues.append(Issue("error", "schema", loc, "files must be an object"))
            continue
        if entry.get("file_count") != len(files):
            issues.append(Issue(
                "error", "schema", loc,
                f"file_count ({entry.get('file_count')!r}) does not match len(files) ({len(files)})",
            ))
        for rel, meta in files.items():
            floc = f"{loc}.files[{rel!r}]"
            if not isinstance(meta, dict):
                issues.append(Issue("error", "schema", floc, "file entry must be an object"))
                continue
            sha = meta.get("sha256")
            if not isinstance(sha, str) or not SHA256_RE.match(sha):
                issues.append(Issue("error", "schema", floc, f"invalid sha256: {sha!r}"))
            size = meta.get("size_bytes")
            if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                issues.append(Issue("error", "schema", floc, f"invalid size_bytes: {size!r}"))

    return manifest, issues


def check_snapshot_id(snapshot_dir: Path, manifest: dict) -> List[Issue]:
    issues: List[Issue] = []
    snapshot_id = manifest.get("snapshot_id")
    if snapshot_dir.name != snapshot_id:
        issues.append(Issue(
            "error", "snapshot_id", str(snapshot_dir),
            f"snapshot directory name {snapshot_dir.name!r} does not match manifest snapshot_id {snapshot_id!r}",
        ))
    return issues


# ---------------------------------------------------------------------------
# profiles/default presence + on-disk correspondence
# ---------------------------------------------------------------------------

def check_profiles_on_disk(snapshot_dir: Path, manifest: dict) -> List[Issue]:
    issues: List[Issue] = []
    profiles = manifest.get("profiles", {})

    default_dir = snapshot_profile_skills_dir(snapshot_dir, DEFAULT_PROFILE)
    if DEFAULT_PROFILE not in profiles:
        pass  # already reported by schema check
    elif not default_dir.is_dir():
        issues.append(Issue("error", "profile", str(default_dir), "profiles/default/skills is missing on disk"))

    for name in profiles:
        skills_dir = snapshot_profile_skills_dir(snapshot_dir, name)
        if not skills_dir.is_dir():
            issues.append(Issue("error", "profile", str(skills_dir), f"profile '{name}' skills directory is missing on disk"))

    profiles_root = snapshot_dir / "profiles"
    if profiles_root.is_dir():
        for entry in sorted(profiles_root.iterdir()):
            if entry.is_dir() and entry.name not in profiles:
                issues.append(Issue(
                    "error", "profile", str(entry),
                    f"directory present on disk but not listed in manifest: {entry.name!r}",
                ))

    return issues


# ---------------------------------------------------------------------------
# File hash + exact manifest/on-disk correspondence + symlink detection
# ---------------------------------------------------------------------------

def check_file_correspondence(snapshot_dir: Path, manifest: dict) -> List[Issue]:
    issues: List[Issue] = []
    profiles = manifest.get("profiles", {})

    for name, entry in profiles.items():
        if not isinstance(entry, dict):
            continue
        skills_root = snapshot_profile_skills_dir(snapshot_dir, name)
        files = entry.get("files", {}) or {}

        if not skills_root.is_dir():
            continue  # already reported by check_profiles_on_disk

        for rel, meta in files.items():
            try:
                full = safe_relpath_join(skills_root, rel)
            except PathSafetyError as exc:
                issues.append(Issue("error", "path_escape", f"{name}:{rel}", str(exc)))
                continue

            if full.is_symlink():
                issues.append(Issue("error", "unsafe_symlink", str(full), "manifest entry resolves to a symlink"))
                continue
            if not full.exists():
                issues.append(Issue("error", "missing_file", str(full), "listed in manifest but missing on disk"))
                continue
            if not full.is_file():
                issues.append(Issue("error", "missing_file", str(full), "manifest entry is not a regular file"))
                continue

            expected_sha = meta.get("sha256") if isinstance(meta, dict) else None
            actual_sha = file_sha256(full)
            if expected_sha and actual_sha != expected_sha:
                issues.append(Issue("error", "hash_mismatch", str(full), f"expected sha256 {expected_sha}, got {actual_sha}"))

            expected_size = meta.get("size_bytes") if isinstance(meta, dict) else None
            actual_size = full.stat().st_size
            if isinstance(expected_size, int) and actual_size != expected_size:
                issues.append(Issue("error", "hash_mismatch", str(full), f"expected size {expected_size}, got {actual_size}"))

        # Detect files/symlinks on disk that aren't listed in the manifest.
        for path, kind in walk_tree(skills_root):
            rel = path.relative_to(skills_root).as_posix()
            if kind == "symlink":
                issues.append(Issue("error", "unsafe_symlink", str(path), "symlink present in snapshot"))
                continue
            if rel not in files:
                issues.append(Issue("error", "extra_file", str(path), "present on disk but not listed in manifest"))

    return issues


def verify_snapshot(snapshot_dir: Path) -> Tuple[Optional[dict], List[Issue]]:
    """Manifest schema/type + snapshot id + hash + on-disk correspondence checks."""
    manifest, issues = load_and_check_manifest_schema(snapshot_dir)
    if manifest is None:
        return None, issues
    issues = list(issues)
    issues += check_snapshot_id(snapshot_dir, manifest)
    issues += check_profiles_on_disk(snapshot_dir, manifest)
    issues += check_file_correspondence(snapshot_dir, manifest)
    return manifest, issues


# ---------------------------------------------------------------------------
# Content-level checks (validate only)
# ---------------------------------------------------------------------------

def check_frontmatter(snapshot_dir: Path, manifest: dict) -> List[Issue]:
    issues: List[Issue] = []
    for name, entry in manifest.get("profiles", {}).items():
        if not isinstance(entry, dict):
            continue
        skills_root = snapshot_profile_skills_dir(snapshot_dir, name)
        for rel in entry.get("files", {}) or {}:
            if Path(rel).name != "SKILL.md":
                continue
            try:
                full = safe_relpath_join(skills_root, rel)
            except PathSafetyError:
                continue
            if not full.is_file():
                continue
            _, errors = parse_skill_frontmatter(full)
            for err in errors:
                issues.append(Issue("error", "frontmatter", str(full), err))
    return issues


def check_secrets(snapshot_dir: Path, manifest: dict, strict: bool = False) -> List[Issue]:
    """
    Scan every manifest-listed file for likely-secret patterns.

    Skill documentation, templates, and examples routinely contain
    token/key-*shaped* strings (e.g. `sk-xxxx...`, `AKIAIOSFODNN7EXAMPLE`,
    `-----BEGIN ... PRIVATE KEY-----\n...`) that are illustrative, not live
    credentials. By default these are reported as *warnings* — visible
    (path + category, never the matched value) but non-blocking — since the
    pattern match alone cannot distinguish a placeholder from a real leak.
    Pass strict=True (hsb-validate's --strict-secrets) to treat every hit as
    a blocking error instead.
    """
    severity = "error" if strict else "warning"
    issues: List[Issue] = []
    for name, entry in manifest.get("profiles", {}).items():
        if not isinstance(entry, dict):
            continue
        skills_root = snapshot_profile_skills_dir(snapshot_dir, name)
        for rel in entry.get("files", {}) or {}:
            try:
                full = safe_relpath_join(skills_root, rel)
            except PathSafetyError:
                continue
            if not full.is_file():
                continue
            for category in scan_file_for_secrets(full):
                issues.append(Issue(severity, "secret", str(full), f"likely secret detected (category={category})"))
    return issues


def check_forbidden_state(snapshot_dir: Path, manifest: dict) -> List[Issue]:
    issues: List[Issue] = []
    for name, entry in manifest.get("profiles", {}).items():
        if not isinstance(entry, dict):
            continue
        for rel in entry.get("files", {}) or {}:
            parts = Path(rel).parts
            basename = parts[-1] if parts else rel
            if basename in FORBIDDEN_STATE_FILENAMES:
                issues.append(Issue("error", "forbidden_state", f"{name}:{rel}", f"forbidden state filename: {basename}"))
            if any(part in FORBIDDEN_STATE_DIRNAMES for part in parts[:-1]):
                issues.append(Issue("error", "forbidden_state", f"{name}:{rel}", "path contains a forbidden internal/runtime directory name"))
    return issues


def validate_snapshot(
    snapshot_dir: Path,
    check_secrets_enabled: bool = True,
    strict_secrets: bool = False,
) -> Tuple[Optional[dict], List[Issue]]:
    """
    Full validation: everything verify_snapshot checks, plus content-level
    checks. Manifest schema, hashes, manifest/on-disk correspondence,
    path/symlink safety, forbidden state, and invalid YAML frontmatter are
    always blocking errors. Likely-secret hits are non-blocking warnings
    unless strict_secrets=True.
    """
    manifest, issues = verify_snapshot(snapshot_dir)
    if manifest is None:
        return None, issues
    issues = list(issues)
    issues += check_frontmatter(snapshot_dir, manifest)
    issues += check_forbidden_state(snapshot_dir, manifest)
    if check_secrets_enabled:
        issues += check_secrets(snapshot_dir, manifest, strict=strict_secrets)
    return manifest, issues
