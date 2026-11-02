---
name: github-pages-sites
description: "Use when building or operating a Jekyll GitHub Pages site."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    category: software-development
    tags: [github-pages, jekyll, documentation, websites]
---

# GitHub Pages doc sites

Class: markdown reference/documentation sites published as Jekyll on GitHub Pages (legacy build, source `main` `/docs`). Repo/PR mechanics (git-workflow.sh, branch protection, betterleaks) live in memory — this skill covers Pages-specific decisions and verification.

## Procedure

1. **Structure:** content in `docs/`; enable Pages with `gh api -X POST repos/<o>/<r>/pages -f "source[branch]=main" -f "source[path]=/docs"`.
2. **Config placement (highest-order rule):** `_config.yml` MUST live inside the Pages source dir (`docs/_config.yml`). Jekyll's default config path is `<source>/_config.yml` — a repo-root config is SILENTLY ignored and the site renders on GitHub's fallback Primer theme with zero build errors. A local build that passes an explicit `--config` flag masks this; never use that crutch — local builds must replicate the deployment invocation exactly (`jekyll build --source docs`, default config lookup).
3. **Theme selection:** the user requires NATIVE search — verify a theme ships search before proposing it. Known: bulma-clean-theme has none in any version; beautiful-jekyll has navbar search (enable with `post_search: true`; the search corpus is built inline from `site.html_pages` in release 6.0.1, so every page needs a title); just-the-docs uses `search_enabled: true`. Pin `remote_theme` to a git tag verified to exist (`gh api repos/<owner>/<repo>/tags`) — release titles don't always match tag names. Project sites need `baseurl: "/<repo>"`.
4. **Layouts:** Jekyll never auto-applies theme layouts. Set a front-matter default — scope `path: ""` + `type: "pages"` → the theme's layout (beautiful-jekyll: `page`; just-the-docs: `default`). Paths in the defaults scope are relative to the SOURCE root, not the repo root: with source `/docs`, scope path `"docs"` matches nothing.
5. **Local verification:** after building, grep the OUTPUT, not the exit code — theme marker class (e.g. `navbar-custom`), the search overlay id (`beautifuljekyll-search-overlay`), search-corpus entry count vs page count, and that new static files (llms.txt) were copied.
6. **Live verification (the rule that outranks all local checks):** after the user merges, poll `gh api repos/<o>/<r>/pages/builds/latest` until `built`, then curl the live URL and grep for the change's marker. A `built` status proves nothing about content — a silently-ignored config builds green forever. Never report a Pages fix as working until the live fetch confirms it.
7. kramdown does not autolink bare URLs in tables/prose — emit `[url](url)` everywhere a link should be clickable.

## Pitfalls

- git-workflow.sh `change` commits only STAGED changes — untracked files are silently left out of the PR. After opening, run `gh pr diff <n> --name-only` and confirm every intended file is in the diff; add strays via `update` on the PR branch.
- Verify what the deployment SERVES after every merge before claiming success — local builds and build status are not evidence of live state.

## References

- `references/llms-txt.md` — recipe for adding llms.txt / llms-full.txt per llmstxt.org.
