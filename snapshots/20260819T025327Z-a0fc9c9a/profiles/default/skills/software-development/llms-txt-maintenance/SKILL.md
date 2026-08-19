---
name: llms-txt-maintenance
description: Generate and maintain llm.txt / llms.txt files for documentation or content sites using deterministic scripts, CI validation, and low-churn update workflows.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [llms-txt, llm-txt, docs, sitemap, ci, github-actions, python, generated-artifacts]
    related_skills: [python-cli-patterns, python-dev, api-governance, openapi-api-designer]
---

# llms.txt Maintenance

## Overview

Use this skill when a user wants a repeatable way to generate or maintain `llm.txt` or `llms.txt` for a website, especially a documentation site, learning portal, or static content site. The goal is to avoid hand-maintained URL inventories and instead produce a deterministic text artifact from stable site signals such as repository metadata or a published sitemap.

This skill is about the **maintenance pattern**, not a single site. It covers generator design, file format discipline, validation, GitHub Actions automation, and compatibility details that reduce churn.

## When to Use

- Generating `llm.txt` or `llms.txt` for a docs site
- Maintaining an existing LLM-discovery text file automatically
- Adding CI checks so generated discovery files stay current
- Choosing between sitemap-driven and repo-metadata-driven generation
- Designing a low-churn GitHub Actions workflow for generated text artifacts

Do not use this skill for:
- General robots.txt or sitemap authoring
- Rich search indexing systems that need embeddings or full-site crawling infra
- One-off manual link lists with no expectation of maintenance

## Core Recommendation

Default to **generated, deterministic, CI-maintained** files.

For most doc sites, the best progression is:

1. start with **published sitemap generation** when the site is static and the sitemap is trustworthy
2. move to **repo-source generation plus sitemap validation** when the repo exposes strong metadata and PR-time correctness matters
3. keep the output deterministic so CI and code review stay quiet

Do not hand-edit page inventories unless the user explicitly wants a tiny, static, curated file.

## Source-of-Truth Decision Rules

### Prefer sitemap-first when:
- the site already publishes a clean `sitemap.xml`
- you need a quick, low-maintenance implementation
- the content changes infrequently or unpredictably
- the goal is to capture published public pages with minimal complexity

### Prefer repo-source generation when:
- the site exposes rich metadata such as titles, navigation order, sections, front matter, or collections
- PR-time validation matters before deploy
- drafts, redirects, or non-reader pages must be excluded intentionally
- the site structure should drive grouping and display order

### Strong default pattern
- **Generate from repo metadata when available**
- **Validate against sitemap** to confirm published URLs match expectations
- Fall back to **sitemap-only generation** when source metadata is weak or unavailable

## File Format Guidance

Keep `llm.txt` / `llms.txt` simple and stable.

Recommended shape:
- site title
- one-line description
- base URL
- grouped section headings
- bullet list of `Title — URL`

Avoid:
- timestamps
- run IDs
- nondeterministic summaries
- decorative prose that adds churn without improving discoverability

If the user asks for `llm.txt`, consider also writing `llms.txt` as an alias when that helps compatibility. Make the alias behavior explicit and optionally disable it with a flag such as `--no-alias`.

## Generator Design Rules

A good generator should:

1. use stable inputs
2. normalize URLs consistently
3. deduplicate canonicals
4. group content into predictable sections
5. sort output deterministically
6. write UTF-8 with `\n` line endings
7. support a `--check` mode for CI
8. exit non-zero when generated output differs in check mode

### Inclusion rules

Typically include:
- documentation pages
- tutorials
- reference guides
- glossary or introduction pages
- examples if they are reader-facing

Typically exclude:
- `404.html`
- feeds
- search pages
- tag/archive listings unless intentionally part of the docs IA
- assets and raw files
- duplicate canonical URLs

## CI / GitHub Actions Pattern

For GitHub Actions, the standard pattern is:

1. checkout repo
2. set up Python
3. run generator
4. run `--check`
5. run lightweight tests or syntax checks
6. commit only if the generated file changed

Recommended triggers:
- `workflow_dispatch`
- weekly schedule by default
- push/PR when the generator or site metadata changes
- optionally post-deploy if the source of truth is the published site

### Cadence

If the user is unsure how often the site changes, start with **weekly**. Increase to daily only when content drift actually warrants it.

## Python Implementation Guidance

Prefer a **dependency-free stdlib script** unless the site genuinely needs HTML parsing, YAML front matter parsing, or richer content extraction. This keeps GitHub Actions simple and durable.

### Compatibility pitfall: newline-stable writes

When forcing `\n` line endings across Python versions, do **not** assume `Path.write_text(..., newline="\n")` is available everywhere. For broad compatibility, prefer:

```python
with path.open("w", encoding="utf-8", newline="\n") as handle:
    handle.write(content)
```

This is the safer choice for scripts that may run on older local interpreters or mixed CI environments.

## Validation Rules

Validation should happen at two levels.

### 1. Structural validation
Check that:
- every entry has a URL
- URLs are absolute if the file is meant for external discovery
- there are no duplicates
- excluded pages are absent
- output order is stable

### 2. Published-site validation
If a sitemap exists, compare generated URLs to it.

Use warnings or failures depending on maturity:
- warn first when adopting the workflow
- fail later once the generator is trusted

## Review Heuristics

Before finishing, confirm:
- the script is deterministic
- the CI workflow will not create noisy commits
- the file name matches the user’s requested convention
- the generator can be run locally and in GitHub Actions
- the validation step matches the chosen source of truth

## Included Support Files

This skill includes:
- `templates/generate_llms_txt.py` — starter Python generator using sitemap-driven discovery
- `templates/maintain-llms-txt.yml` — starter GitHub Actions workflow
- `references/implementation-notes.md` — notes on source selection, determinism, and compatibility pitfalls

## Common Pitfalls

1. Hand-editing the file instead of generating it.
2. Including timestamps, which creates noisy commits.
3. Using nondeterministic summaries in CI.
4. Forgetting `--check`, so CI cannot detect drift.
5. Generating from the published site when repo metadata is the real source of truth.
6. Generating from repo metadata without validating against what is actually published.
7. Assuming a single filename convention without checking whether `llm.txt`, `llms.txt`, or both are needed.
8. Writing newline-normalized output with APIs that are not available across the Python versions likely to execute the script.

## Verification Checklist

- [ ] Chosen source of truth is explicit: sitemap, repo metadata, or both
- [ ] Output is deterministic and low-churn
- [ ] `--check` mode exists and exits non-zero on drift
- [ ] GitHub Actions workflow only commits when content changed
- [ ] Validation matches the actual publication model of the site
- [ ] The requested filename convention (`llm.txt`, `llms.txt`, or both) is handled explicitly
