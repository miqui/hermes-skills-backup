"""Render and publish concise skill deltas for full-snapshot pull requests.

Snapshots remain complete, standalone restore artifacts. This module compares a
new snapshot manifest to its immediate predecessor and emits a compact review
summary containing only new, modified, and removed skill roots.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Callable, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from hermes_skills_backup.common import MANIFEST_FILENAME, list_snapshot_ids, read_manifest

COMMENT_MARKER = "<!-- hermes-skills-backup:delta -->"
GitHubRequest = Callable[[str, str, str, object | None], object]


def _manifest_files(manifest: Mapping[str, object]) -> dict[tuple[str, str], Mapping[str, object]]:
    """Return manifest file metadata keyed by ``(profile, relative_path)``."""
    files: dict[tuple[str, str], Mapping[str, object]] = {}
    profiles = manifest.get("profiles", {})
    if not isinstance(profiles, Mapping):
        return files
    for profile, profile_data in profiles.items():
        if not isinstance(profile, str) or not isinstance(profile_data, Mapping):
            continue
        profile_files = profile_data.get("files", {})
        if not isinstance(profile_files, Mapping):
            continue
        for relpath, metadata in profile_files.items():
            if isinstance(relpath, str) and isinstance(metadata, Mapping):
                files[(profile, relpath)] = metadata
    return files


def _skill_roots(files: Iterable[tuple[str, str]]) -> set[tuple[str, str]]:
    """Return ``(profile, root)`` pairs for every manifest SKILL.md file."""
    return {
        (profile, str(Path(relpath).parent).replace("\\", "/"))
        for profile, relpath in files
        if Path(relpath).name == "SKILL.md"
    }


def _containing_skill(
    profile: str,
    relpath: str,
    roots: Iterable[tuple[str, str]],
) -> tuple[str, str] | None:
    """Find the deepest skill root containing a changed file, if any."""
    candidates = [
        (root_profile, root)
        for root_profile, root in roots
        if root_profile == profile and (relpath == root or relpath.startswith(f"{root}/"))
    ]
    return max(candidates, key=lambda entry: len(entry[1]), default=None)


def snapshot_delta(base_manifest: Mapping[str, object], current_manifest: Mapping[str, object]) -> dict[str, list[str]]:
    """Classify changed files into new, modified, removed, and unscoped roots."""
    base_files = _manifest_files(base_manifest)
    current_files = _manifest_files(current_manifest)
    base_roots = _skill_roots(base_files)
    current_roots = _skill_roots(current_files)

    added_files = set(current_files) - set(base_files)
    removed_files = set(base_files) - set(current_files)
    modified_files = {
        key for key in set(base_files) & set(current_files) if base_files[key] != current_files[key]
    }

    new_roots = current_roots - base_roots
    removed_roots = base_roots - current_roots
    changed_common_roots: set[tuple[str, str]] = set()
    unscoped: set[str] = set()

    all_roots = base_roots | current_roots
    for profile, relpath in added_files | removed_files | modified_files:
        root = _containing_skill(profile, relpath, all_roots)
        if root is None:
            unscoped.add(f"{profile}/{relpath}")
        elif root not in new_roots and root not in removed_roots:
            changed_common_roots.add(root)

    def labels(roots: Iterable[tuple[str, str]]) -> list[str]:
        return [f"{profile}/{root}" for profile, root in sorted(roots)]

    return {
        "new": labels(new_roots),
        "modified": labels(changed_common_roots),
        "removed": labels(removed_roots),
        "unscoped": sorted(unscoped),
    }


def _render_section(title: str, values: list[str]) -> list[str]:
    if not values:
        return []
    lines = [f"### {title} ({len(values)})"]
    lines.extend(f"- `{value}`" for value in values)
    return lines + [""]


def build_delta_comment(snapshots_dir: Path, snapshot_ids: Iterable[str]) -> str:
    """Build Markdown review text for each changed snapshot ID.

    The predecessor is selected from the existing, lexicographically ordered
    snapshot IDs. Snapshot IDs are timestamp-prefixed, so this is their
    chronological order without recording host-specific paths or state.
    """
    snapshots_dir = snapshots_dir.resolve()
    available_ids = list_snapshot_ids(snapshots_dir)
    blocks = [
        COMMENT_MARKER,
        "## Corpus skill delta",
        "",
        "Full snapshots are retained for standalone verification and restore. "
        "This review summary lists only skill roots that changed.",
        "",
    ]

    for snapshot_id in sorted(set(snapshot_ids)):
        if snapshot_id not in available_ids:
            raise FileNotFoundError(f"Snapshot not found: {snapshots_dir / snapshot_id}")
        position = available_ids.index(snapshot_id)
        current_manifest = read_manifest(snapshots_dir / snapshot_id / MANIFEST_FILENAME)
        blocks.extend([f"## Snapshot `{snapshot_id}`", ""])

        if position == 0:
            blocks.extend(["No prior snapshot is available for a delta comparison.", ""])
            continue

        base_id = available_ids[position - 1]
        base_manifest = read_manifest(snapshots_dir / base_id / MANIFEST_FILENAME)
        delta = snapshot_delta(base_manifest, current_manifest)
        blocks.extend([f"Compared with `{base_id}`.", ""])
        blocks.extend(_render_section("New skills", delta["new"]))
        blocks.extend(_render_section("Modified skills", delta["modified"]))
        blocks.extend(_render_section("Removed skills", delta["removed"]))
        blocks.extend(_render_section("Unscoped snapshot files", delta["unscoped"]))
        if not any(delta.values()):
            blocks.extend(["No file-level changes were found relative to the prior snapshot.", ""])

    blocks.extend(["_Generated by `hermes-skills-backup` from manifest hashes._", ""])
    return "\n".join(blocks)


def _github_request(method: str, url: str, token: str, payload: object | None = None) -> object:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "hermes-skills-backup",
            **({"Content-Type": "application/json"} if data is not None else {}),
        },
    )
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - GitHub API URL is CI-configured.
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"GitHub API request failed with HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError("GitHub API request failed") from exc


def upsert_pull_request_comment(
    api_base: str,
    repository: str,
    pull_request_number: int,
    token: str,
    body: str,
    request_json: GitHubRequest = _github_request,
) -> str:
    """Create or update the single marker-owned delta comment for a PR."""
    api_base = api_base.rstrip("/")
    issue_base = f"{api_base}/repos/{repository}/issues/{pull_request_number}/comments"
    existing = request_json("GET", f"{issue_base}?per_page=100", token)
    if not isinstance(existing, list):
        raise RuntimeError("GitHub API comments response was not a list")

    for comment in existing:
        if isinstance(comment, Mapping) and COMMENT_MARKER in str(comment.get("body", "")):
            comment_id = comment.get("id")
            if not isinstance(comment_id, int):
                raise RuntimeError("GitHub API comment had no numeric id")
            request_json("PATCH", f"{api_base}/repos/{repository}/issues/comments/{comment_id}", token, {"body": body})
            return "updated"

    request_json("POST", issue_base, token, {"body": body})
    return "created"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hsb-pr-delta",
        description="Post a concise manifest-derived skill delta to a pull request.",
    )
    parser.add_argument("--snapshots-dir", type=Path, default=Path("snapshots"), metavar="DIR")
    parser.add_argument("--snapshot-id", action="append", dest="snapshot_ids", metavar="ID")
    parser.add_argument("--pull-request-number", type=int, default=None, metavar="NUMBER")
    args = parser.parse_args(argv)

    snapshot_ids = args.snapshot_ids or [
        item for item in os.environ.get("SNAPSHOT_IDS", "").splitlines() if item
    ]
    if not snapshot_ids:
        parser.error("one or more --snapshot-id values or SNAPSHOT_IDS is required")

    pull_request_number = args.pull_request_number
    if pull_request_number is None:
        raw_number = os.environ.get("PULL_REQUEST_NUMBER", "")
        if not raw_number.isdigit():
            parser.error("--pull-request-number or numeric PULL_REQUEST_NUMBER is required")
        pull_request_number = int(raw_number)

    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not repository:
        parser.error("GITHUB_TOKEN and GITHUB_REPOSITORY are required")

    body = build_delta_comment(args.snapshots_dir, snapshot_ids)
    action = upsert_pull_request_comment(
        api_base=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
        repository=repository,
        pull_request_number=pull_request_number,
        token=token,
        body=body,
    )
    print(f"✓ Delta PR comment {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
