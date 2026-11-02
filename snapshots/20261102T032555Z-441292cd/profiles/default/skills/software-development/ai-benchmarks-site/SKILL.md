---
name: ai-benchmarks-site
description: Use when working on the AI-benchmarks GitHub Pages site.
version: 1.0.0
category: software-development
---

# AI-benchmarks site (miqui/AI-benchmarks)

Durable markdown reference of AI leaderboards/benchmarks, served at https://miqui.github.io/AI-benchmarks/. Also the playbook for debugging Jekyll/GitHub-Pages theme builds. Original content source: Miguel's Perplexity research export (cached at ~/.hermes/cache/scratch/ai-benchmarks-source.md, pruned after 72h).

## Repo layout
- Mr. Green Jekyll theme v1.3.2 (MrGreensWorkshop/MrGreen-JekyllTheme). Jekyll source = repo ROOT; content pages are *.md at root; URLs pinned via `permalink` (e.g. /coding-agents/, /bug-hunt/).
- Sidebar/top nav is DATA-driven from `_data/nav/pages.yml` (title/icon/url entries, in display order) — `nav_order` frontmatter does NOT drive this theme's nav. Every new page needs BOTH the .md file AND a nav entry; a page missing from pages.yml renders fine at its URL but appears nowhere in the menu, which reads to the user as 'don't see <page> on the site'.
- GitHub Pages: legacy build, source = main branch path `/`. CRITICAL: Pages reads _config.yml from the SOURCE dir — when source was /docs, the root _config.yml was silently ignored and three theme PRs appeared to do nothing. Never trust a theme change until the live site is checked.
- llms.txt + llms-full.txt at repo root (serve at /AI-benchmarks/llms.txt). Regenerate llms-full.txt by concatenating all *.md (strip frontmatter; `## Title` + `Source:` URL per page).
- Search config in _data/conf/main.yml: `search_enable: true`, `search_with_uri: false` (simple binding mode — reliable), `search_disable_auto_search: false` (live results while typing).

## Theme quirks (learned the hard way)
- The theme PATCHES its vendored simple-jekyll-search (auto-search-while-typing disabled + clear-on-empty). With `search_disable_auto_search: true`, typing does nothing — results only appear on form submit.
- _includes/default/search.html originally hid results 100ms after input blur; mousedown on a result blurs the input first, so the pending click never lands ("list generates but can't navigate"). Fixed with a document-level click-outside handler — do NOT reintroduce onblur/onfocusout timers.
- Owner branding lives in _data/owner/en.yml (brand, brand_sub_text, name, meta description) — shipped as "Your Brand"/"Sample" placeholders. Avatar: _data/conf/main.yml `side_nav_profile_img_path` prepends site.baseurl to the path, so self-host the image under assets/img/ (miqui-avatar.jpg); hotlinked URLs break.
- remote_theme tag pins vary per repo: daattali/beautiful-jekyll uses @6.0.1 (no v prefix — @v6.0.1 404s). Always check the repo's actual git tag before pinning.
- bulma-clean-theme has NO search in any version (feature list, no /search/ demo page). Before switching themes for Miguel: confirm must-have features (search etc.) against the theme's docs/demo and flag constraints upfront — he picks by looks and wants limitations surfaced before adopting.

## Verify before PR (mandatory)
- Build exactly like Pages: docker run ruby:3.2, install bundler + Gemfile deps, `bundle exec jekyll build --safe`. NEVER pass --config explicitly — it masks source-dir config mismatches (this false-verified a build once).
- For search/UI changes: serve the output (python http.server, symlink dir so baseurl paths map) and drive it in a real browser via CDP (real key + mouse events): type query → results render live → real mouse click (mousePressed, ~150ms, mouseReleased) → correct page loads.
- Then `betterleaks dir .`, then git-workflow.sh change/update (see memory). Miguel merges; after merge verify the LIVE site (pages builds/latest status + curl) before claiming success. Pages quirks: changing the source path (PUT /pages) does NOT trigger a build — force one with POST /repos/<o>/<r>/pages/builds; a build queued seconds before a config change still runs with the old config (race → confusing failures).