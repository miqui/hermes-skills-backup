# Implementation notes for llm.txt / llms.txt maintenance

## Source selection

A sitemap-driven generator is the best first implementation when:
- the site is static
- the sitemap is reliable
- content change frequency is unknown
- the user wants a low-maintenance GitHub Actions workflow quickly

A repo-metadata-driven generator becomes the better long-term choice when:
- titles and section grouping should mirror the docs IA exactly
- drafts and redirects need intentional exclusion
- validation should happen before deploy in PRs

## Determinism rules

Keep the artifact review-friendly:
- no timestamps
- no build IDs
- no model-generated summaries in CI
- stable section ordering
- stable title ordering within section
- stable URL normalization and dedupe

## GitHub Actions pattern

Use this order:
1. generate file(s)
2. run syntax/tests
3. run `--check`
4. commit only when files changed

Suggested default schedule: weekly.

## Python compatibility note

For newline-stable writes across mixed Python versions, prefer:

```python
with path.open("w", encoding="utf-8", newline="\n") as handle:
    handle.write(content)
```

This avoids relying on `Path.write_text(..., newline=...)`, which is not uniformly available on older interpreters that may still appear in local validation environments.

## Filename convention

If the user explicitly asks for `llm.txt`, honor that. Optionally emit `llms.txt` as an alias when compatibility is useful. Make alias generation switchable with a flag such as `--no-alias`.
