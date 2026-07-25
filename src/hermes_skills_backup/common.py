"""
Shared constants, path/profile helpers, hashing, secret scanning, and YAML
frontmatter parsing used by every hermes-skills-backup entry point.

Design goals
------------
* Genuine YAML parsing (PyYAML) for SKILL.md frontmatter — no hand-rolled
  regex parsing of YAML.
* All filesystem walks are symlink-safe: symlinked files/dirs are never
  followed or included, preventing snapshot/restore path escapes.
* Secrets detection returns only (path, category) tuples — the matched
  value itself is never surfaced.
* Manifests never record hostnames, absolute source paths, OS details, or
  credentials.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets as _secrets_mod
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

import yaml

from hermes_skills_backup import __version__

# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------
MANIFEST_FILENAME = "MANIFEST.json"
RESTORE_FILENAME = "RESTORE.md"
PROFILES_DIRNAME = "profiles"
SKILLS_DIRNAME = "skills"
DEFAULT_PROFILE = "default"
SCHEMA_VERSION = 1
GENERATOR_NAME = "hermes-skills-backup"

SNAPSHOT_ID_RE = re.compile(r"^\d{8}T\d{6}Z-[0-9a-f]{8}$")
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# Hidden entries that sit directly at the root of a skills directory (or a
# Hermes home) and represent internal/runtime bookkeeping rather than skill
# content. These are pruned when *walking the top level only* — nested,
# legitimately hidden skill assets (e.g. a skill shipping its own
# `.golangci.yml`) are preserved.
NESTED_JUNK_DIRNAMES = {".git", "__pycache__"}

# Exact Hermes-home-root state filenames. These never legitimately belong
# inside a skills tree; validate re-checks their absence anywhere in a
# snapshot as defense in depth against a misconfigured --source/--hermes-home.
FORBIDDEN_STATE_FILENAMES = {
    ".env", "auth.json", "auth.lock", "config.yaml", "gateway_state.json",
    "state.db", "state.db-shm", "state.db-wal", "kanban.db",
    "kanban.db.dispatch.lock", "kanban.db.init.lock",
    "verification_evidence.db", "channel_directory.json",
    "models_dev_cache.json", "provider_models_cache.json",
    "ollama_cloud_models_cache.json", "slack-manifest.json",
    ".hermes_history", ".update_check", ".skills_prompt_snapshot.json",
    ".bundled_manifest", ".curator_state", ".usage.json", ".usage.json.lock",
    ".DS_Store",
}
# Directory names that are unambiguous indicators of leaked internal/VCS
# state if found anywhere in a snapshot's file listing.
FORBIDDEN_STATE_DIRNAMES = {".curator_backups", ".hub", ".git", "__pycache__"}

REQUIRED_SKILL_FIELDS = ("name", "description")

_TEXT_EXTENSIONS = {
    ".md", ".txt", ".yaml", ".yml", ".toml", ".json", ".py", ".sh", ".bash",
    ".ini", ".cfg", ".js", ".ts", ".rb", ".go", ".rs", ".env", ".csv",
    ".xml", ".html", ".conf",
}
_MAX_SCAN_BYTES = 5 * 1024 * 1024  # skip huge/binary files for secret scan

# category -> compiled pattern
SECRET_PATTERNS: List[Tuple[str, "re.Pattern[str]"]] = [
    ("generic_credential_assignment", re.compile(
        r'(?i)\b(api[-_]?key|secret[-_]?key|access[-_]?token|auth[-_]?token'
        r'|password|private[-_]?key|client[-_]?secret)\b\s*[=:]\s*'
        r'["\']?[A-Za-z0-9/_\-+=]{8,}'
    )),
    ("openai_style_key", re.compile(r'\bsk-[A-Za-z0-9]{20,}\b')),
    ("github_token", re.compile(r'\bgh[pousr]_[A-Za-z0-9]{36,}\b')),
    ("aws_access_key_id", re.compile(r'\bAKIA[0-9A-Z]{16}\b')),
    ("private_key_block", re.compile(
        r'-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'
    )),
    ("slack_token", re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{10,}\b')),
]


class SecretsDetected(RuntimeError):
    """Raised when likely secrets are found. Carries (path, category) only."""

    def __init__(self, offenders: List[Tuple[str, str]]) -> None:
        self.offenders = offenders
        lines = "\n".join(f"  {path} [{category}]" for path, category in offenders)
        super().__init__(f"Likely secrets detected — aborting.\n{lines}")


class PathSafetyError(ValueError):
    """Raised when a path escapes its expected base directory."""


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------

def default_hermes_home() -> Path:
    return Path.home() / ".hermes"


def list_snapshot_ids(snapshots_dir: Path) -> "list[str]":
    """Return the sorted ids of every snapshot directory under snapshots_dir."""
    if not snapshots_dir.is_dir():
        return []
    return sorted(
        p.name for p in snapshots_dir.iterdir()
        if p.is_dir() and (p / MANIFEST_FILENAME).is_file()
    )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_snapshot_id() -> str:
    """Timestamp + random suffix. Never includes hostname or OS details."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = _secrets_mod.token_hex(4)
    return f"{ts}-{suffix}"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65_536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Symlink-safe tree walking
# ---------------------------------------------------------------------------

def walk_tree(root: Path) -> Iterator[Tuple[Path, str]]:
    """
    Yield (path, kind) for every entry under *root*, where kind is
    "file" or "symlink". Symlinked directories are reported but never
    descended into, so nothing outside *root* can be reached.
    """
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        cur = Path(dirpath)
        for d in sorted(dirnames):
            full = cur / d
            if full.is_symlink():
                yield full, "symlink"
        # prevent os.walk from descending into symlinked directories
        dirnames[:] = [d for d in sorted(dirnames) if not (cur / d).is_symlink()]
        for fn in sorted(filenames):
            full = cur / fn
            yield (full, "symlink") if full.is_symlink() else (full, "file")


def iter_included_files(skills_root: Path) -> Iterator[Path]:
    """
    Yield files that should be included in a snapshot from *skills_root*:
    hidden (dot-prefixed) entries directly at the root are excluded, as are
    nested VCS/build junk dirs and symlinks anywhere. Everything else —
    including nested dotfiles that are genuine skill assets — is preserved.
    """
    for dirpath, dirnames, filenames in os.walk(skills_root, followlinks=False):
        cur = Path(dirpath)
        rel_parts = cur.relative_to(skills_root).parts
        is_root = len(rel_parts) == 0

        kept_dirs = []
        for d in sorted(dirnames):
            if is_root and d.startswith("."):
                continue
            if d in NESTED_JUNK_DIRNAMES:
                continue
            if (cur / d).is_symlink():
                continue
            kept_dirs.append(d)
        dirnames[:] = kept_dirs

        for fn in sorted(filenames):
            if is_root and fn.startswith("."):
                continue
            full = cur / fn
            if full.is_symlink():
                continue
            yield full


def find_symlinks(skills_root: Path) -> List[Path]:
    """Return every symlink found under skills_root (for warnings)."""
    return [p for p, kind in walk_tree(skills_root) if kind == "symlink"]


# ---------------------------------------------------------------------------
# Profile discovery
# ---------------------------------------------------------------------------

def discover_profiles(hermes_home: Path) -> "dict[str, Path]":
    """
    Return {profile_name: skills_dir} for every profile that has a
    non-empty skills directory under *hermes_home*:
      default          -> <hermes_home>/skills
      <profile-name>    -> <hermes_home>/profiles/<profile-name>/skills
    Profiles without a skills directory are omitted.
    """
    profiles: "dict[str, Path]" = {}

    default_skills = hermes_home / SKILLS_DIRNAME
    if default_skills.is_dir() and not default_skills.is_symlink():
        profiles[DEFAULT_PROFILE] = default_skills

    profiles_root = hermes_home / PROFILES_DIRNAME
    if profiles_root.is_dir() and not profiles_root.is_symlink():
        for entry in sorted(profiles_root.iterdir()):
            if not entry.is_dir() or entry.is_symlink():
                continue
            if not SAFE_NAME_RE.match(entry.name) or entry.name.startswith("."):
                continue
            skills_dir = entry / SKILLS_DIRNAME
            if skills_dir.is_dir() and not skills_dir.is_symlink():
                profiles[entry.name] = skills_dir

    return profiles


def profile_source_skills_dir(hermes_home: Path, profile_name: str) -> Path:
    """Map a profile name to its skills dir under a Hermes home (source or restore target)."""
    if profile_name == DEFAULT_PROFILE:
        return hermes_home / SKILLS_DIRNAME
    return hermes_home / PROFILES_DIRNAME / profile_name / SKILLS_DIRNAME


def snapshot_profile_skills_dir(snapshot_dir: Path, profile_name: str) -> Path:
    """Every profile — including default — lives at profiles/<name>/skills inside a snapshot."""
    return snapshot_dir / PROFILES_DIRNAME / profile_name / SKILLS_DIRNAME


def profile_skills_rel_path(profile_name: str) -> str:
    return f"{PROFILES_DIRNAME}/{profile_name}/{SKILLS_DIRNAME}"


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------

def safe_relpath_join(base: Path, relpath: str) -> Path:
    """
    Join *relpath* (a manifest-style POSIX relative path) onto *base*,
    raising PathSafetyError if it is absolute, contains traversal
    components, or would resolve outside *base*.
    """
    if not relpath or relpath in (".", ".."):
        raise PathSafetyError(f"invalid relative path: {relpath!r}")
    posix = relpath.replace("\\", "/")
    if posix.startswith("/") or (len(posix) > 1 and posix[1] == ":"):
        raise PathSafetyError(f"absolute path not allowed: {relpath!r}")
    parts = posix.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise PathSafetyError(f"path traversal not allowed: {relpath!r}")

    joined = base.joinpath(*parts)
    resolved_base = base.resolve()
    resolved_joined = joined.resolve()
    if resolved_joined != resolved_base and resolved_base not in resolved_joined.parents:
        raise PathSafetyError(f"path escapes base directory: {relpath!r}")
    return joined


_SYSTEM_DIR_NAMES = {
    "/", "/etc", "/usr", "/bin", "/sbin", "/var", "/System", "/Library",
    "/Applications", "/root", "/opt", "/proc", "/dev", "/boot", "/private",
    "/home", "/tmp",
    # macOS aliases /tmp, /var, /etc to /private/... via a top-level symlink;
    # block the resolved forms too so the shallow well-known dirs can't be
    # reached by resolving through it.
    "/private/etc", "/private/var", "/private/tmp",
}


def is_dangerous_target(target: Path) -> Optional[str]:
    """
    Return a human-readable reason if *target* is an unsafe/ambiguous
    restore destination, else None.

    Shallowness and the system-directory blocklist are evaluated against
    the *unresolved* (symlink-preserving) path, since on macOS common,
    benign temp-dir roots like /tmp are themselves symlinks (-> /private/tmp)
    and resolving them would misreport a legitimate subdirectory like
    /tmp/my-test-home as too shallow. The target itself (not its ancestors)
    is separately rejected if it is a symlink.
    """
    expanded = target.expanduser()
    normalized = Path(os.path.normpath(str(expanded.absolute())))
    resolved = expanded.resolve(strict=False)

    if normalized == Path(normalized.anchor) or resolved == Path(resolved.anchor):
        return "target is a filesystem root"
    if resolved == Path.home().resolve():
        return "target is the user's home directory"
    if str(normalized) in _SYSTEM_DIR_NAMES or str(resolved) in _SYSTEM_DIR_NAMES:
        return f"target is a well-known system directory ({normalized})"
    if len(normalized.parts) < 3:
        return "target path is too shallow / ambiguous"
    if resolved.exists() and not resolved.is_dir():
        return "target exists and is not a directory"
    if expanded.is_symlink():
        return "target is a symlink"

    return None


# ---------------------------------------------------------------------------
# Secrets detection
# ---------------------------------------------------------------------------

def scan_file_for_secrets(path: Path) -> List[str]:
    """Return the list of secret *categories* (never values) found in a file."""
    if path.suffix.lower() not in _TEXT_EXTENSIONS:
        return []
    try:
        if path.stat().st_size > _MAX_SCAN_BYTES:
            return []
        text = path.read_text(errors="replace")
    except OSError:
        return []

    found = []
    for category, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            found.append(category)
    return found


def scan_tree_for_secrets(files: List[Path]) -> List[Tuple[str, str]]:
    """Return [(str(path), category), ...] for every hit across *files*."""
    offenders: List[Tuple[str, str]] = []
    for f in files:
        for category in scan_file_for_secrets(f):
            offenders.append((str(f), category))
    return offenders


# ---------------------------------------------------------------------------
# YAML frontmatter (genuine PyYAML parsing)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*(\n|$)", re.DOTALL)


def extract_frontmatter_block(text: str) -> Optional[str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    return m.group(1)


def parse_skill_frontmatter(path: Path) -> Tuple[Optional[dict], List[str]]:
    """
    Parse a SKILL.md file's YAML frontmatter using PyYAML.
    Returns (data_or_None, error_messages).
    """
    errors: List[str] = []
    try:
        text = path.read_text(errors="replace")
    except OSError as exc:
        return None, [f"cannot read file: {exc}"]

    block = extract_frontmatter_block(text)
    if block is None:
        return None, ["missing YAML frontmatter block (expected leading --- ... ---)"]

    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        return None, [f"invalid YAML frontmatter: {exc}"]

    if not isinstance(data, dict):
        return None, ["frontmatter did not parse to a YAML mapping"]

    for field in REQUIRED_SKILL_FIELDS:
        value = data.get(field)
        if field not in data:
            errors.append(f"missing required frontmatter field: '{field}'")
        elif not isinstance(value, str) or not value.strip():
            errors.append(f"empty or non-string required frontmatter field: '{field}'")

    return data, errors


# ---------------------------------------------------------------------------
# Manifest I/O
# ---------------------------------------------------------------------------

def compute_profile_files(skills_root: Path) -> "dict[str, dict]":
    files: "dict[str, dict]" = {}
    for path in iter_included_files(skills_root):
        rel = path.relative_to(skills_root).as_posix()
        files[rel] = {
            "sha256": file_sha256(path),
            "size_bytes": path.stat().st_size,
        }
    return dict(sorted(files.items()))


def assemble_manifest(
    profile_files: "dict[str, dict]",
    snapshot_id: str,
    created_utc: str,
) -> dict:
    """
    profile_files: {profile_name: {rel: {"sha256":..., "size_bytes":...}}}
    Builds the full MANIFEST.json document. Never records hostnames,
    absolute source paths, OS details, or credentials.
    """
    profiles = {}
    for name in sorted(profile_files):
        files = profile_files[name]
        profiles[name] = {
            "skills_path": profile_skills_rel_path(name),
            "file_count": len(files),
            "files": files,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "created_utc": created_utc,
        "generator": {"name": GENERATOR_NAME, "version": __version__},
        "profiles": profiles,
    }


def write_manifest(manifest: dict, dest: Path) -> None:
    dest.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def read_manifest(path: Path) -> dict:
    return json.loads(path.read_text())


def write_restore_md(manifest: dict, dest: Path) -> None:
    profile_names = sorted(manifest.get("profiles", {}))
    lines = [
        "# Restore Instructions",
        "",
        f"Snapshot ID: `{manifest.get('snapshot_id', '?')}`",
        f"Created (UTC): {manifest.get('created_utc', '?')}",
        f"Profiles included: {', '.join(profile_names) if profile_names else '(none)'}",
        "",
        "This snapshot was produced by the `hermes-skills-backup` project and can be",
        "restored with its `hsb-restore` command-line tool.",
        "",
        "## Dry run (default — makes no changes)",
        "",
        "```",
        "hsb-restore \\",
        "  --snapshots-dir <path-to-snapshots-dir> \\",
        f"  --snapshot-id {manifest.get('snapshot_id', '<snapshot-id>')} \\",
        "  --target-hermes-home <path-to-target-hermes-home>",
        "```",
        "",
        "## Apply the restore",
        "",
        "```",
        "hsb-restore \\",
        "  --snapshots-dir <path-to-snapshots-dir> \\",
        f"  --snapshot-id {manifest.get('snapshot_id', '<snapshot-id>')} \\",
        "  --target-hermes-home <path-to-target-hermes-home> \\",
        "  --apply",
        "```",
        "",
        "Restoring rebuilds, per profile:",
        "",
        "- `default` → `<target-hermes-home>/skills`",
        "- `<profile-name>` → `<target-hermes-home>/profiles/<profile-name>/skills`",
        "",
        "Data is staged in a temporary directory and verified before anything under",
        "the target Hermes home is replaced. Nothing outside the target Hermes home",
        "is ever modified or removed.",
        "",
        "Before restoring, verify the snapshot's integrity with `hsb-verify` and",
        "`hsb-validate`.",
        "",
    ]
    dest.write_text("\n".join(lines))
