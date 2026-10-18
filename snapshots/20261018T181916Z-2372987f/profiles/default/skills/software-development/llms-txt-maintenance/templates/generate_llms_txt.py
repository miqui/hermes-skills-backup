#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

SITE_NAME = "example.com"
BASE_URL = "https://example.com"
DEFAULT_SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
DESCRIPTION = "Public documentation and learning resources."

SECTION_LABELS = {
    "": "Core pages",
    "docs": "Documentation",
    "guides": "Guides",
    "reference": "Reference",
    "examples": "Examples",
}

TITLE_OVERRIDES = {
    f"{BASE_URL}/": "Home",
}

EXCLUDED_URLS = {
    f"{BASE_URL}/404.html",
}

SECTION_ORDER = {
    "Core pages": 0,
    "Documentation": 1,
    "Guides": 2,
    "Reference": 3,
    "Examples": 4,
    "Other": 99,
}


@dataclass(frozen=True)
class Page:
    url: str
    title: str
    section: str


def normalize_url(url: str) -> str:
    cleaned = url.strip().split("#", 1)[0]
    if cleaned.endswith("/index.html"):
        cleaned = cleaned[: -len("/index.html")] + "/"
    return cleaned


def infer_title(url: str) -> str:
    if url in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[url]

    path = url.removeprefix(BASE_URL).strip("/")
    if path.endswith(".html"):
        path = path[: -len(".html")]
    leaf = path.split("/")[-1] if path else "home"
    return " ".join(word.capitalize() for word in leaf.replace("-", " ").replace("_", " ").split())


def infer_section(url: str) -> str:
    path = url.removeprefix(BASE_URL).strip("/")
    if not path:
        return "Core pages"
    first_segment = path.split("/", 1)[0]
    return SECTION_LABELS.get(first_segment, "Other")


def fetch_sitemap_urls(sitemap_url: str) -> list[str]:
    with urllib.request.urlopen(sitemap_url, timeout=30) as response:
        xml_bytes = response.read()

    root = ET.fromstring(xml_bytes)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    seen: set[str] = set()
    urls: list[str] = []

    for loc in root.findall(".//sm:loc", namespace):
        if not (loc.text or "").strip():
            continue
        url = normalize_url(loc.text or "")
        if url in EXCLUDED_URLS or url in seen:
            continue
        seen.add(url)
        urls.append(url)

    if not urls:
        raise SystemExit(f"No URLs found in sitemap: {sitemap_url}")

    return urls


def build_pages(urls: Iterable[str]) -> list[Page]:
    pages = [Page(url=url, title=infer_title(url), section=infer_section(url)) for url in urls]
    return sorted(
        pages,
        key=lambda page: (SECTION_ORDER.get(page.section, 50), page.section.lower(), page.title.lower(), page.url),
    )


def render_content(pages: Iterable[Page]) -> str:
    grouped: dict[str, list[Page]] = defaultdict(list)
    for page in pages:
        grouped[page.section].append(page)

    section_names = sorted(grouped, key=lambda name: (SECTION_ORDER.get(name, 50), name.lower()))
    lines = [
        f"# {SITE_NAME}",
        "",
        f"> {DESCRIPTION}",
        "",
        f"Base URL: {BASE_URL}",
        "",
        "This file is generated from the public sitemap.",
        "Do not edit manually.",
        "",
    ]

    for section in section_names:
        lines.append(f"## {section}")
        for page in grouped[section]:
            lines.append(f"- {page.title} — {page.url}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_if_changed(path: pathlib.Path, content: str) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == content:
        return False
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return True


def check_up_to_date(path: pathlib.Path, content: str) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    return existing == content


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate llm.txt / llms.txt from sitemap.xml")
    parser.add_argument("--sitemap-url", default=DEFAULT_SITEMAP_URL)
    parser.add_argument("--output", default="llm.txt")
    parser.add_argument("--alias-output", default="llms.txt")
    parser.add_argument("--no-alias", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    content = render_content(build_pages(fetch_sitemap_urls(args.sitemap_url)))
    primary = pathlib.Path(args.output)
    alias = pathlib.Path(args.alias_output)

    if args.check:
        if not check_up_to_date(primary, content):
            print(f"{primary} is out of date", file=sys.stderr)
            return 1
        if not args.no_alias and not check_up_to_date(alias, content):
            print(f"{alias} is out of date", file=sys.stderr)
            return 1
        print("Generated files are up to date")
        return 0

    changed = False
    changed = write_if_changed(primary, content) or changed
    if not args.no_alias:
        changed = write_if_changed(alias, content) or changed

    print("Updated files" if changed else "No changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
