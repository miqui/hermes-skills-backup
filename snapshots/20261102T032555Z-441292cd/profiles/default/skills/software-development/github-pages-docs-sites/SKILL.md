---
name: github-pages-docs-sites
description: "Use when publishing markdown as a GitHub Pages site."
version: 1.0.0
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [github-pages, jekyll, docs, static-site]
    category: software-development
---

# GitHub Pages docs sites

Publish a repo of markdown files as a GitHub Pages project site — reference
collections, handbooks, indexes. Default stack: Jekyll + just-the-docs
remote theme (sidebar nav, built-in client-side search, zero infra). All
depth lives in `references/publishing.md` — read it before the first build
of a site or when diagnosing a broken one.

## Always-on rules

- Give every docs page the theme layout via front-matter `defaults` in
  `_config.yml`, never per-page: Jekyll does NOT auto-apply layouts to
  pages, and a missing `layout: default` renders raw HTML with no sidebar,
  no search, and no theme JS even when `search_enabled: true`.
- Never emit bare URLs in kramdown markdown — the default renderer does not
  autolink them, so table-cell and bullet URLs render as plain text. Write
  `[label](url)` for every link, and grep generated pages for bare URLs
  before shipping.
- Verify a site by fetching the served HTML (`curl -sI` for 200 + grep for
  expected content strings), never by trusting the config or the build
  status alone.
- Keep build artifacts (`_site/`, `.jekyll-cache/`, `Gemfile.lock`)
  gitignored and out of commits.

## Procedure

1. Scaffold: `docs/` markdown source + root `_config.yml` with
   `remote_theme`, `search_enabled`, front-matter defaults for `docs/`
   (full config in `references/publishing.md`).
2. Create/enable the repo and push via the user's standard repo workflow
   (`git-workflow.sh`, betterleaks gate, protect main — see the
   `software-development/github` skill). Enable Pages from main, `/docs`
   path: `gh api -X POST repos/<o>/<r>/pages -f "source[branch]=main" -f
   "source[path]=/docs"`.
3. Poll `gh api repos/<o>/<r>/pages` until status `built`; diagnose failures
   via `/pages/builds/latest`.
4. Verify live: `curl -sI https://<owner>.github.io/<repo>/` → 200, plus a
   content grep. Theme-asset 404s on a project page mean a layout/config
   problem, not a CDN issue.
5. Optional local check: build in Docker (the `jekyll/jekyll:4` image lacks
   `jekyll-remote-theme` and `jekyll-include-cache` — install both inline).
   Mount output under `/Users/` — Docker Desktop on macOS cannot mount
   `/var/folders` (TMPDIR); the mount succeeds silently but output
   vanishes.
