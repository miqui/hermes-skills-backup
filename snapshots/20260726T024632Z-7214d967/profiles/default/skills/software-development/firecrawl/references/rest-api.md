# Firecrawl REST API Quick Reference

Use this reference when Firecrawl should be used without installing the CLI or skills package, or when an application should call Firecrawl directly over HTTP.

## When to Use

- the user does not want a CLI install
- the integration belongs in application code
- the agent needs direct API usage examples or endpoint routing guidance
- a lightweight smoke test is needed with plain HTTP

## Requirements

You still need a Firecrawl API key.

- Environment variable example: `FIRECRAWL_API_KEY=fc-...`
- Auth header: `Authorization: Bearer fc-YOUR_API_KEY`
- Base URL: `https://api.firecrawl.dev/v2`

## Primary Endpoints

- `POST /search` — discover pages by query; can return results with optional content
- `POST /scrape` — extract clean markdown from a known URL
- `POST /interact` — perform browser actions on live pages
- `POST /support/ask` — diagnose a failing Firecrawl call with `{ question, jobId? }`
- `POST /support/docs-search` — ask product-doc questions and receive answers with citations

## Endpoint Routing Heuristic

Choose the endpoint based on the actual product need:

- Use `/search` when the feature starts with a query and must discover pages first.
- Use `/scrape` when the URL is already known.
- Use `/interact` when the target page requires clicks, forms, or navigation beyond plain extraction.
- Use `/support/ask` when a Firecrawl job failed or returned confusing output and you have a `jobId`.
- Use `/support/docs-search` when the question is about Firecrawl behavior, docs, or product capabilities.

## Example cURL Patterns

### Scrape a known URL

```bash
curl -sS https://api.firecrawl.dev/v2/scrape \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://firecrawl.dev"}'
```

### Search for pages

```bash
curl -sS https://api.firecrawl.dev/v2/search \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"firecrawl docs scrape api"}'
```

### Ask support about a failed job

```bash
curl -sS https://api.firecrawl.dev/v2/support/ask \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"Why did this scrape fail?","jobId":"job_..."}'
```

### Ask docs-search a product question

```bash
curl -sS https://api.firecrawl.dev/v2/support/docs-search \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"How does Firecrawl handle interact jobs?"}'
```

## Verification

For a no-install smoke test, run one real request against the endpoint that matches the intended feature. Do not treat env-var wiring alone as success.

## References

- API docs: `https://docs.firecrawl.dev`
- Skills repo: `https://github.com/firecrawl/skills`
- CLI repo: `https://github.com/firecrawl/cli`
- Workflow repo: `https://github.com/firecrawl/firecrawl-workflows`

## Pitfalls

1. Using `/interact` when `/scrape` is sufficient.
2. Guessing at retries instead of sending failures to `/support/ask` with `jobId`.
3. Testing only configuration and never making a real request.
4. Mixing live-session usage guidance with product-code integration guidance.
