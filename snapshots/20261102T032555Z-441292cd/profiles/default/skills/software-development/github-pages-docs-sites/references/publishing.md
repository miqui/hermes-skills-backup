# Publishing a GitHub Pages docs site

Target shape: a repo of markdown files served at
`https://<owner>.github.io/<repo>/` with sidebar navigation and search.
Default theme: just-the-docs (remote theme). Project pages serve under
`/<repo>/` — the theme handles baseurl itself.

## Config template

```yaml
title: My Site
description: One-line description.
remote_theme: just-the-docs/just-the-docs
search_enabled: true
heading_anchors: true
nav_sort: pages
permalink: pretty

plugins:
  - jekyll-remote-theme

defaults:
  - scope:
      path: "docs"
    values:
      layout: default

aux_links:
  "GitHub repo":
    - "https://github.com/<o>/<r>"
```

- `defaults` is the load-bearing part: every page under the scoped path gets
  `layout: default`. Per-page frontmatter then only carries `title`,
  `nav_order`, `parent` (for grouped nav), `permalink`.
- `permalink: pretty` makes `docs/foo.md` serve as `foo.html`; index page
  sets `permalink: /`.

## Content rules

- kramdown does NOT autolink bare URLs. Emit `[label](https://…)` always;
  reusing the URL as its own label (`[https://x](https://x)`) is acceptable
  for generated tables. Catch stragglers:

```bash
grep -rnE '(^|\s)https?://[^\s|)]' docs/   # ignore matches already inside ](...)
```

- Tables are the commonest offender: a bare URL in a table cell renders as
  plain text with no link styling.
- Each reference page: what it is, link, one-line "what it tells you",
  caveats; end capability pages with usage guidance.

## Enable, build, verify

```bash
# Enable Pages from main, /docs path ("already exists" = fine)
gh api -X POST repos/<o>/<r>/pages -f "source[branch]=main" -f "source[path]=/docs"

# Poll until built; diagnose failures here
gh api repos/<o>/<r>/pages --jq '{status, html_url}'
gh api repos/<o>/<r>/pages/builds/latest --jq '{status, error}'

# Real end-to-end check
curl -sI https://<owner>.github.io/<repo>/ | head -3
curl -s https://<owner>.github.io/<repo>/ | grep -i '<expected-string>'

# Layout/search sanity on the served page
curl -s https://<owner>.github.io/<repo>/ | grep -c jtd-search
```

- A build status of `built` only means Jekyll compiled — it does not mean
  pages use the theme layout. The `jtd-search` grep is the real check.
- Theme-asset 404s (e.g. `/assets/js/just-the-docs.js`) on a project page
  correlate with the missing-layout problem, not a CDN outage.

## Local build (Docker, no local Jekyll)

```bash
docker run --rm -e JEKYLL_UID=$(id -u) \
  -v "$PWD":/srv/jekyll \
  -v /Users/<you>/<shared-path>:/tmp/out \
  jekyll/jekyll:4 sh -c "gem install jekyll-remote-theme jekyll-include-cache -N >/dev/null && \
    jekyll build --destination /tmp/out"
```

- The `jekyll/jekyll:4` image ships neither `jekyll-remote-theme` nor its
  dependency `jekyll-include-cache`; install both inline or the build dies
  with a Dependency Error.
- Docker Desktop on macOS cannot mount `/var/folders` (TMPDIR's home) — the
  `-v` mount succeeds but output vanishes. Mount output under `/Users/`.
- Sass deprecation warnings from just-the-docs are harmless; judge the run
  by the final `done in Ns` line and the output file list.

## Pages limits (check before adding heavy content)

- Repo ≤1GB, published site ≤1GB, 100GB/month soft bandwidth cap, 10-min
  build ceiling. A pure-markdown site is trivially within all of them — note
  the limits in the site README so future image/PDF content gets checked.
