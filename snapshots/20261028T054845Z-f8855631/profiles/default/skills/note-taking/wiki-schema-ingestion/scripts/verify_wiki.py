#!/usr/bin/env python3
"""
Verification script for SCHEMA.md-style wikis.

Usage: python3 verify_wiki.py <wiki_repo_root> <touched_page_1> [<touched_page_2> ...]

Checks:
  - frontmatter parses + tags in taxonomy + `updated` bumped to today (warn only)
  - raw/ files: sha256 of body matches frontmatter
  - wikilinks in touched pages resolve + each page has >=2
  - index.md "Total pages" matches actual entity/concept/comparison/query file count

Run from repo root, e.g.:
  python3 verify_wiki.py . concepts/foo.md concepts/bar.md
"""
import re
import os
import sys
import glob
import hashlib
import datetime

try:
    import yaml
except ImportError:
    print("Requires PyYAML: pip install pyyaml")
    sys.exit(1)


def load_taxonomy(schema_path):
    tags = set()
    schema = open(schema_path).read()
    for m in re.finditer(r'`([a-z-]+)`\s*—', schema):
        tags.add(m.group(1))
    return tags


def check_frontmatter(path, allowed_tags):
    content = open(path).read()
    m = re.match(r'^---\n(.*?)\n---\n', content, re.S)
    assert m, f"{path}: no frontmatter"
    fm = yaml.safe_load(m.group(1))
    for tag in fm.get('tags', []):
        assert tag in allowed_tags, f"{path}: tag '{tag}' not in taxonomy"
    updated = str(fm.get('updated'))
    today = datetime.date.today().isoformat()
    if updated != today:
        print(f"  WARN {path}: updated={updated} != today ({today}) — bump if this was actually edited today")
    return fm


def check_raw_hash(path):
    content = open(path).read()
    idx1 = content.find('---\n')
    idx2 = content.find('---\n', idx1 + 4)
    fm_raw = content[idx1 + 4:idx2]
    body = content[idx2 + 4:]
    h = hashlib.sha256(body.encode('utf-8')).hexdigest()
    assert f"sha256: {h}" in fm_raw, f"{path}: hash mismatch (computed {h})"
    print(f"  OK raw hash {path}: {h}")


def check_wikilinks(path, all_pages):
    content = open(path).read()
    links = re.findall(r'\[\[([a-z0-9-]+)\]\]', content)
    assert len(links) >= 2, f"{path}: fewer than 2 wikilinks ({len(links)})"
    for l in set(links):
        assert l in all_pages, f"{path}: links to missing page '{l}'"
    print(f"  OK wikilinks {path}: {sorted(set(links))}")


def main():
    root = sys.argv[1]
    touched = sys.argv[2:]
    os.chdir(root)

    allowed_tags = load_taxonomy('SCHEMA.md')

    all_pages = set()
    for d in ['entities', 'concepts', 'comparisons', 'queries']:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith('.md'):
                    all_pages.add(f[:-3])

    print("=== Frontmatter + tags ===")
    for p in touched:
        if p.startswith('raw/'):
            continue
        check_frontmatter(p, allowed_tags)
        print(f"  OK frontmatter {p}")

    print("=== Raw file hashes ===")
    for p in touched:
        if p.startswith('raw/'):
            check_raw_hash(p)

    print("=== Wikilinks ===")
    for p in touched:
        if p.startswith('raw/'):
            continue
        check_wikilinks(p, all_pages)

    print("=== index.md page count ===")
    idx = open('index.md').read()
    m = re.search(r'Total pages: (\d+)', idx)
    stated = int(m.group(1))
    actual = len(all_pages)
    status = "OK" if stated == actual else "MISMATCH"
    print(f"  {status}: index says {stated}, actual file count is {actual}")

    print("\nAll checks completed.")


if __name__ == '__main__':
    main()
