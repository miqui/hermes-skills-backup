# llms.txt recipe (llmstxt.org)

Purpose: an `/llms.txt` at the site root tells LLM crawlers what the site contains and links each page; `llms-full.txt` carries the full contents. Both are plain static files for Jekyll.

## Steps

1. Write `docs/llms.txt` (source dir — static files are copied verbatim; `.txt` is not processed by Jekyll):
   - H1 = site name; one blockquote paragraph = what the site is for.
   - `## Docs` section: one `- [Page Title](absolute-url): one-line what-this-page-tells-you` per page. Absolute URLs (`https://<user>.github.io/<repo>/<slug>/`) avoid baseurl ambiguity.
   - Write curated one-liners per page (what the page actually tells you), not title echoes — that is the value of the file.
   - End with an `## Optional` section linking `llms-full.txt`.
2. Generate `docs/llms-full.txt` by script: strip front-matter (`---` blocks) from each source `.md`, emit `## <Page Title>` + `Source: <absolute url>` + body, one page per section, skip the llms files themselves.
3. Verify in the local build output: both files exist at the output root; after merge, `curl https://<site>/llms.txt` returns the H1.

## Notes

- llms-full.txt grows with content (~2KB/page here); trivially inside GitHub Pages limits at any realistic size.
- GitHub serves `.txt` files as plain `text/plain` — no configuration needed.
