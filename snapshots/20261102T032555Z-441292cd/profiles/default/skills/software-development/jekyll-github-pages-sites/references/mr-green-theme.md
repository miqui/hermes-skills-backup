# Mr. Green theme (MrGreensWorkshop/MrGreen-JekyllTheme)

Condensed quirks for sites built on Mr. Green (verified against tag v1.3.2).

## Install model

- Fork-based TEMPLATE, not a remote theme: ships its own `_config.yml`, `_data/` (conf + owner + lang), and expects source = repo ROOT. Adopting it means restructuring the repo to its layout — it cannot be applied with one config line.
- Gemfile pins `github-pages` → legacy Pages build works from repo root; only whitelisted plugins (jekyll-paginate, jekyll-redirect-from). No Actions deploy needed.
- Strip the demo/multilingual content when adopting (language dirs, `_posts`, `tabs/`, `privacy-policy.md`, README-* variants) but KEEP the infrastructure files.

## Search stack — the quirks that cost time

- `query/search.json` (frontmatter `layout: json/search`) is REQUIRED infrastructure, not demo scaffolding — it generates the search data. Deleting the `query/` dir kills search silently.
- The theme patches its vendored simple-jekyll-search: with `search_disable_auto_search: true` in `_data/conf/main.yml`, typing does NOT search — results only render on form submit (Enter). With it `false`, results render live while typing.
- The theme's search box hides results 100ms after the input's `blur` and clears the query on `focusout` — a mousedown on a result blurs the input first, so the click is canceled before it lands ("list generates but can't navigate"). Replace blur/timeout hiding with a document-level click-outside handler on `#searchbox-form`.
- `search_with_uri: true` (async fetch → object binding) produced a dead binding in practice; keep `search_with_uri: false` so the simple path binds at load with the URL string.
- The search result template and corpus are built inline per page from `site.html_pages` — verify the built pages carry the site's real page URLs (baseurl-prefixed), not the theme demo's.

## Branding/owner config

- `_data/owner/en.yml` holds `brand`, `brand_sub_text` (`$site_sample` renders the placeholder word "Sample" from `_data/lang/en.yml`), `name`, `meta_common_description` — replace all placeholders.
- Side-nav profile image: `side_nav_profile_img_path` in `_data/conf/main.yml` is prepended with `site.baseurl` by the include, so hotlinked external URLs break — self-host the image under `assets/img/`.
- `$site_*` tokens in owner/language YAML resolve from `_data/conf/main.yml` replacement settings (`sample_replace`, `brand_replace`).
