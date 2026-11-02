---
name: jekyll-github-pages-sites
version: 1.0.0
description: "Use when building or debugging GitHub Pages Jekyll sites."
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [jekyll, github-pages, themes, verification]
    category: software-development
---

# Jekyll GitHub Pages sites

Procedure for building, re-theming, and debugging a GitHub Pages Jekyll site. Deliver every change through the repo's standard PR flow and never merge yourself.

## Before claiming any change is done — verify the RENDERED site

- After every deploy-affecting merge, fetch the LIVE page HTML (and key assets) and confirm the expected markup (theme classes, feature elements) before reporting success. A `built` Pages status or a passing local build does NOT prove the theme/layout applied — Pages silently falls back to its default theme when config is ignored, with zero build errors.
- Fetch with a distinct request per check (page HTML, asset URL status, data files) and grep for feature-specific markup. Report only what the fetches actually showed.

## Config location — the silent-ignores trap

- GitHub Pages reads `_config.yml` from the Pages SOURCE directory. With source set to a subfolder (e.g. `/docs`), a repo-root `_config.yml` is silently ignored and the site renders on GitHub's default theme with no build error. Put the config inside the source dir, or repoint the Pages source to the folder the config lives in.
- When testing config-location behavior locally, never pass `--config` explicitly — that masks the exact mismatch. Replicate Pages' invocation: `jekyll build --safe` with the default config lookup from `--source`.

## Theme selection gate (do this BEFORE switching)

- Verify the candidate theme natively supports every feature the user requires (e.g. search) from its feature list/docs/demo — if it lacks one, say so and let the user pick again instead of planning a workaround.
- Identify the install model first: `remote_theme` with a pinned tag (works on legacy Pages builds) vs fork-based template (requires restructuring the repo to the template's layout and its own config/data files) vs Actions-based deploy. Report the structural cost before proceeding with a fork-based theme.
- Pin `remote_theme:` to the exact tag and check the repo's real tag name — some repos tag `6.0.1` where the release is titled `v6.0.1`, and the wrong form 404s in the remote-theme fetch.
- For each feature, confirm the wiring in the pinned tag, not on the theme's master branch — unreleased fixes/features don't exist for you.

## Local verification recipe (replicates Pages)

```bash
mkdir -p <output-dir-outside-repo>
docker run --rm -v "$PWD":/srv/jekyll -v <output-dir>:<out-mount> ruby:3.2 bash -lc \
  'gem install bundler --no-document && bundle install && bundle exec jekyll build --safe --destination <out-mount>'
```

- Mount output OUTSIDE the repo; Docker Desktop cannot mount `/var/folders` — only `/Users/...` paths work as mounts.
- The `github-pages` gem + `--safe` is the authentic match for legacy Pages builds; `jekyll/jekyll:4` containers are only a sanity check (different Jekyll major).
- Jekyll treats paths in `defaults.scope` as relative to the SOURCE root, not the repo root.
- kramdown does not autolink bare URLs — bare URLs in markdown tables/bullets render as plain text; emit `[url](url)` links.
- After build, grep the OUTPUT: expected theme classes, feature markup, and that generated data files (e.g. search corpus) contain the site's real pages with correct baseurl-prefixed URLs.

## JS-driven features (search, overlays) — verify interaction, not just markup

- Presence of the search box/overlay markup proves nothing. Drive the real page (CDP keyboard + mouse events) and confirm: the feature initializes from the page's own load path (not a manually re-created instance — that masks a dead binding), results appear, and clicking a result actually navigates.
- Watch for click-cancellation races: handlers that hide a dropdown on input `blur` with a short setTimeout cancel the pending click on the hidden element. Prefer a document-level click-outside handler over blur/timeout hiding.

## Pages API quirks

- `PUT /repos/{o}/{r}/pages` (change source/branch) applies the config but does NOT trigger a rebuild. Force one with `POST /repos/{o}/{r}/pages/builds`.
- In-flight Pages builds may not appear in the Actions list at all; and after a failed build the API can keep reporting a stale `building` — check the latest `pages build and deployment` workflow run's conclusion and `--log-failed` for the real state.
- A build queued moments before a source-config change runs with the OLD config — after repointing source, always force a fresh build and confirm the run's log shows the new `Source:` path.

## Theme-specific depth

- `references/mr-green-theme.md` — Mr. Green (MrGreensWorkshop/MrGreen-JekyllTheme) structure, config knobs, and the search-stack quirks (patched simple-jekyll-search, required `query/search.json`, blur-race fix).
