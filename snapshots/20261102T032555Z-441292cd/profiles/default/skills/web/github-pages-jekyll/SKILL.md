---
name: github-pages-jekyll
description: Use when building or debugging a GitHub Pages Jekyll site.
version: 1.0.0
---

# GitHub Pages Jekyll

## Config location (silent-failure trap)
- Legacy Pages build reads `_config.yml` from the **source directory** (repo root, `/docs`, whatever Pages source is set to). A config at repo root is **silently ignored** when the source is `/docs` — the site renders with the fallback `jekyll-theme-primer` (`markdown-body` markup, `<title>Page | RepoName</title>`, no sidebar/search) with **zero build errors**.
- Symptom check on the live HTML: stylesheet is `assets/css/style.css?v=<sha>`, `<body>` carries no theme classes.

## Local verification
- Replicate the exact Pages invocation: `jekyll build --source <srcdir> --safe` under the `github-pages` gem. Do NOT pass `--config` pointing outside the source dir — it masks config-location bugs (this cost a whole session: local builds passed while Pages ignored the config).
- Authentic env: Docker `ruby:3.2` + `bundle install` on a Gemfile pinning `github-pages`. `jekyll/jekyll:4` is only a weak sanity check (Jekyll 4 vs Pages 3.9/3.10).
- Verify against the BUILT output (theme classes, search data, served static files), and after every merge verify what Pages actually serves — never trust a local build alone.

## remote_theme vs fork-style templates
- Pin `remote_theme` to a tag that exists as a **git tag** (e.g. `daattali/beautiful-jekyll@6.0.1`, not `@v6.0.1` — release titles can add a `v` the tag lacks).
- Fork-style templates (Mr. Green `MrGreensWorkshop/MrGreen-JekyllTheme`) are full root-sourced sites with `_data/` config — NOT remote_theme-able; adopt by restructuring the repo into the template layout.
- When stripping a template's demo content, keep its feature infrastructure: Mr. Green's site search needs the `search_enable` toggle PLUS the `query/search.json` data page (`layout: json/search`); deleting that file breaks search silently while the UI still renders.
- Fork-style templates drive navigation from `_data/` files, not page frontmatter: a new page may need an explicit entry in the nav data file (e.g. `_data/nav/pages.yml`). A page missing there renders at its URL but shows nowhere in the menu — the user reports it as 'not on the site'.
- After adopting a template, grep `_data/language/` and `_data/owner/` for placeholder strings (`Your Brand`, `Sample`, `$site_*` substitution tokens) — they surface in navbar, page `<title>`, side-nav sub-text, and meta tags long after the demo pages are gone.
- Theme search toggles are easy to get wrong: just-the-docs search never rendered because pages lacked the theme layout (defaults scope path must be relative to the source root — `path: "docs"` never matches when the source IS `docs/`); beautiful-jekyll needs `post_search: true`.

## Deploy mechanics
- Changing Pages config/source (`PUT /repos/{o}/{r}/pages`) does **not** trigger a rebuild — force one with `POST /repos/{o}/{r}/pages/builds`.
- A build queued just before a source change still runs with the old source (race) — check the run log's `Source:` line, not just the commit.
- `pages/builds/latest` can report a stale `building` after a run already failed — cross-check the Actions run (`pages build and deployment`) for the real conclusion. In-progress Pages runs may not appear in the Actions UI until the runner picks them up.
- Legacy build failure signature `No such file or directory @ dir_chdir0 - /github/workspace/docs` = SCSS conversion running with a source dir that no longer exists (stale source path or deleted docs/).