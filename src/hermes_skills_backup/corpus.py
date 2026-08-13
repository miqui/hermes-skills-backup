"""
Generates the `skills-corpus.json` D3 corpus artifact for a snapshot.

Schema mirrors d3-hermes-skill-corpus's `scripts/generate-corpus.mjs` /
`src/types.ts` (`SkillCorpus`, `SkillRecord`, `CorpusNode`) exactly enough
for that app's UI to consume the file: `generatedAt`, `sourceRoot`, `stats`,
`skills`, `tree`.

Records are always built from an already-staged/copied skills directory
(never the live source) so the corpus can never drift from what a given
snapshot actually contains, and so re-running against mutated live skills
after the fact cannot change a past snapshot's corpus.

No metadata is invented: `author`/`version`/`tags`/`relatedSkills`/
`description` fall back to the D3 generator's own defaults ("" / []) when a
skill's frontmatter doesn't provide them — never fabricated.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

import yaml

_HEADING_RE = re.compile(r"^#\s+", re.MULTILINE)
_CODE_FENCE_RE = re.compile(r"```[\s\S]*?```")
_MD_LINK_RE = re.compile(r"\[(.*?)\]\((.*?)\)")
_DECOR_CHARS_RE = re.compile(r"[>*_`#-]")
_WHITESPACE_RE = re.compile(r"\s+")


def _parse_frontmatter_and_body(text: str) -> Tuple[dict, str]:
    """Mirrors generate-corpus.mjs's parseFrontmatter: tolerant, never raises."""
    if not text.startswith("---\n"):
        return {}, text.strip()

    closing_idx = text.find("\n---\n", 4)
    if closing_idx == -1:
        return {}, text.strip()

    yaml_block = text[4:closing_idx]
    body = text[closing_idx + 5:].strip()

    try:
        frontmatter = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        return {}, body
    if not isinstance(frontmatter, dict):
        frontmatter = {}
    return frontmatter, body


def _summarize_body(body: str) -> str:
    """Mirrors generate-corpus.mjs's summarizeBody exactly (220-char cap)."""
    cleaned = _HEADING_RE.sub("", body, count=1)
    cleaned = _CODE_FENCE_RE.sub(" ", cleaned)
    cleaned = _MD_LINK_RE.sub(r"\1", cleaned)
    cleaned = _DECOR_CHARS_RE.sub(" ", cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned[:220]


def _extract_str_list(frontmatter: dict, key: str) -> List[str]:
    metadata = frontmatter.get("metadata") if isinstance(frontmatter, dict) else None
    hermes = metadata.get("hermes") if isinstance(metadata, dict) else None
    values = hermes.get(key) if isinstance(hermes, dict) else None
    if isinstance(values, list):
        return [v for v in values if isinstance(v, str)]
    return []


def _file_modified_at_iso(path: Path) -> str:
    dt = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _make_root_node() -> dict:
    return {"id": "root", "name": "Hermes Skills", "type": "root", "path": ".", "children": []}


def _ensure_path_node(root: dict, segments: List[str]) -> dict:
    current = root
    accumulated = ""
    for segment in segments:
        accumulated = f"{accumulated}/{segment}" if accumulated else segment
        child = next(
            (c for c in current["children"] if c["name"] == segment and c["type"] == "group"),
            None,
        )
        if child is None:
            child = {
                "id": f"group:{accumulated}",
                "name": segment,
                "type": "group",
                "path": accumulated,
                "children": [],
            }
            current["children"].append(child)
            current["children"].sort(key=lambda n: n["name"])
        current = child
    return current


def _count_nodes(node: dict) -> int:
    return 1 + sum(_count_nodes(c) for c in node.get("children", []))


def _max_depth(node: dict, depth: int = 0) -> int:
    children = node.get("children") or []
    if not children:
        return depth
    return max(_max_depth(c, depth + 1) for c in children)


def build_skill_records(skills_root: Path) -> List[dict]:
    """
    Build SkillRecord dicts from every SKILL.md under an already-staged/copied
    *skills_root* (a snapshot's own copy — never a live source tree).
    """
    skill_paths = sorted(
        (p for p in skills_root.rglob("SKILL.md") if p.is_file()),
        key=lambda p: p.relative_to(skills_root).as_posix(),
    )

    records = []
    for skill_path in skill_paths:
        rel_file = skill_path.relative_to(skills_root).as_posix()
        skill_dir = "/".join(rel_file.split("/")[:-1])
        segments = [s for s in skill_dir.split("/") if s]
        group_segments = segments[:-1]
        folder_name = segments[-1] if segments else skill_path.stem

        text = skill_path.read_text(errors="replace")
        frontmatter, body = _parse_frontmatter_and_body(text)

        name = frontmatter.get("name")
        records.append({
            "id": "/".join(segments),
            "slug": folder_name,
            "name": name if isinstance(name, str) and name else folder_name,
            "folderName": folder_name,
            "categoryPath": group_segments,
            "path": skill_dir,
            "skillFile": rel_file,
            "description": frontmatter.get("description") if isinstance(frontmatter.get("description"), str) else "",
            "author": frontmatter.get("author") if isinstance(frontmatter.get("author"), str) else "",
            "version": frontmatter.get("version") if isinstance(frontmatter.get("version"), str) else "",
            "tags": _extract_str_list(frontmatter, "tags"),
            "relatedSkills": _extract_str_list(frontmatter, "related_skills"),
            "summary": _summarize_body(body),
            "modifiedAt": _file_modified_at_iso(skill_path),
        })
    return records


def build_tree(records: List[dict]) -> dict:
    root = _make_root_node()
    for skill in records:
        parent = _ensure_path_node(root, skill["categoryPath"])
        parent["children"].append({
            "id": f"skill:{skill['id']}",
            "name": skill["name"],
            "type": "skill",
            "path": skill["path"],
            "skillId": skill["id"],
            "description": skill["description"],
            "tags": skill["tags"],
            "relatedSkills": skill["relatedSkills"],
        })
        parent["children"].sort(key=lambda n: n["name"])
    return root


def build_corpus(skills_root: Path, source_root_label: str, generated_at: str) -> dict:
    """
    Build the full SkillCorpus document from an already-staged skills
    directory. *source_root_label* is a snapshot-relative path (never an
    absolute/live filesystem path) recorded as `sourceRoot`.
    """
    records = build_skill_records(skills_root)
    tree = build_tree(records)
    return {
        "generatedAt": generated_at,
        "sourceRoot": source_root_label,
        "stats": {
            "skillCount": len(records),
            "nodeCount": _count_nodes(tree),
            "maxDepth": _max_depth(tree),
        },
        "skills": records,
        "tree": tree,
    }
