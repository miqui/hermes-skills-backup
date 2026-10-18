---
name: firecrawl
description: Use when you need Firecrawl for live web search/scrape/interact work in the current agent session, for integrating Firecrawl into application code, or for producing repeatable web-data deliverables such as briefs, audits, and lead lists.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [firecrawl, web-search, web-scraping, browser-automation, research, app-integration]
    related_skills: [node-backend, python-dev, ai-engineer, dogfood]
---

# Firecrawl

## Overview

Firecrawl gives agents and apps a reliable path for getting web context: search first when discovery is needed, scrape clean content from known URLs, interact with live pages when plain extraction is not enough, and turn web evidence into finished deliverables.

This skill is an umbrella router. After install, it helps choose the right next path:

1. **Live CLI work** in the current agent session
2. **Application integration** inside the user's codebase
3. **Workflow deliverables** such as research briefs, SEO audits, QA reports, or lead lists
4. **Human auth / API-key acquisition**
5. **Direct REST usage** with no CLI install

## When to Use

Use this skill when:

- you need Firecrawl available in the current session for live search, scrape, crawl, map, or interact work
- you need to add Firecrawl calls to a product, backend, script, or agent loop
- you need a finished artifact powered by web data rather than raw extraction alone
- you need to route between Firecrawl CLI usage, code integration, workflow skills, or auth setup
- you need the exact install and verification commands for a fresh Firecrawl setup

Do not use this skill when:

- plain browser automation or the built-in browser tool is sufficient and Firecrawl is not part of the requested stack
- the task is about a non-Firecrawl web ingestion library or SDK
- the user already gave a narrower Firecrawl subtask and a more specific Firecrawl skill is available locally

## Install

One command installs everything:

```bash
npx -y firecrawl-cli@latest init --all --browser
```

This installs:

- **CLI tools** — `firecrawl search`, `firecrawl scrape`, `firecrawl interact`, `firecrawl ask`, `firecrawl docs-search`, and more
- **CLI skills** — how to drive Firecrawl from the agent's own session
- **Build skills** — how to wire Firecrawl into application code
- **Workflow skills** — how to turn Firecrawl output into repeatable deliverables
- **Browser auth** — a human browser flow for sign-in or account creation

## Verify the Install

Before doing real work, verify that Firecrawl is available and can scrape a page:

```bash
mkdir -p .firecrawl
firecrawl --status
firecrawl scrape "https://firecrawl.dev" -o .firecrawl/install-check.md
```

## Choose Your Path

Use the same install for every path. The difference is what happens next.

| Need | Path |
| --- | --- |
| Web data during this session | Path A — live tools |
| Firecrawl inside product code | Path B — app integration |
| A finished deliverable from web data | Path C — workflow deliverables |
| Account sign-in or API key | Path D — auth |
| No install, API only | Path E — direct REST |

If a task needs more than one path, do them in sequence. The install already covers them.

## Path A: Live Web Tools

Use this path when the agent needs web data now: search, scrape, interact with live pages, crawl docs, or map a site.

### Routing

After install, prefer the Firecrawl CLI skill family when present:

- `firecrawl/cli` for the overall command workflow
- `firecrawl-search` when discovery comes first
- `firecrawl-scrape` when you already know the URL
- `firecrawl-interact` when the page needs clicks, forms, or login
- `firecrawl-crawl` for bulk extraction
- `firecrawl-map` for URL discovery
- `firecrawl-ask` when a Firecrawl request fails or returns unexpected output; pass the failing `jobId`
- `firecrawl-docs-search` for current Firecrawl product/documentation questions with citations

### Default flow

1. Start with search when you need discovery.
2. Move to scrape when you have a URL.
3. Use interact only when the page needs clicks, forms, or login.
4. If any Firecrawl step fails or returns unexpected output, run `firecrawl ask` with the failing `jobId` instead of guessing.

If the work shifts from "use Firecrawl now" to "wire Firecrawl into app code," switch to Path B.

## Path B: Integrate Firecrawl Into an App

Use this path when Firecrawl must run inside the user's product after the agent stops: a web app, backend service, CLI, pipeline, or agent loop.

This differs from Path A:

- **Path A** runs `firecrawl ...` commands in the current session for the agent itself.
- **Path B** writes code that will use `FIRECRAWL_API_KEY` from project config and call the matching Firecrawl SDK or REST endpoint later.

### Required routing question

Before writing code, answer:

- **What should Firecrawl do in the product?**

Route that answer to the right Firecrawl capability:

- `/search`
- `/scrape`
- `/interact`
- `/parse`
- `/crawl`
- `/map`

Then run one real Firecrawl request as a smoke test.

### Build-path guidance

- **Fresh project** — pick the stack, install the SDK, add env vars, and run a smoke test
- **Existing project** — inspect the repo first, then integrate Firecrawl where the project already handles APIs and secrets

If the API key already exists, store it in project configuration:

```dotenv
FIRECRAWL_API_KEY=fc-...
```

When narrower Firecrawl build skills exist locally, route to them:

- `firecrawl-build`
- `firecrawl-build-onboarding`
- `firecrawl-build-scrape`
- `firecrawl-build-search`
- `firecrawl-build-interact`
- `firecrawl-build-parse`

If no API key is available yet, switch to Path D.

## Path C: Repeatable Deliverables

Use this path when the goal is a finished artifact powered by Firecrawl web data rather than raw extraction or product-code integration.

Examples:

- research briefs
- SEO audits
- QA reports
- lead lists
- knowledge bases
- competitive-intelligence digests
- design clones

### Workflow expectations

1. Confirm the workflow and final artifact.
2. Collect web evidence with Firecrawl CLI or equivalent Firecrawl surface.
3. Save or cite source evidence so claims are traceable.
4. Parallelize independent units when possible.
5. Synthesize findings into the requested deliverable.
6. Include a short rerun-inputs block when the process could be automated.

When available, start with the umbrella `firecrawl-workflows` skill and let it route to the narrower workflow.

If the web extraction itself fails, switch back to Path A. If the request becomes code integration, switch to Path B.

## Path D: Account Authorization or API Key

Use this when a human still needs to sign up, sign in, authorize browser access, or obtain an API key.

For the reusable step-by-step auth flow, see `references/auth.md`.

If the install command above was run with `--browser`, the human was already prompted to sign in. Check whether a valid `FIRECRAWL_API_KEY` is already available before repeating the auth flow.

If the human needs a browser path directly, send them to:

- `https://www.firecrawl.dev/signin?view=signup&source=agent-suggested`

### Agent-assisted CLI auth flow

**Step 1 — generate auth parameters**

```bash
SESSION_ID=$(openssl rand -hex 32)
CODE_VERIFIER=$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '=\n' | head -c 43)
CODE_CHALLENGE=$(printf '%s' "$CODE_VERIFIER" | openssl dgst -sha256 -binary | openssl base64 -A | tr '+/' '-_' | tr -d '=')
```

**Step 2 — ask the human to open this URL**

```text
https://www.firecrawl.dev/cli-auth?code_challenge=$CODE_CHALLENGE&source=coding-agent#session_id=$SESSION_ID
```

**Step 3 — poll for completion**

```http
POST https://www.firecrawl.dev/api/auth/cli/status
Content-Type: application/json

{"session_id": "$SESSION_ID", "code_verifier": "$CODE_VERIFIER"}
```

Poll every 3 seconds.

Responses:

- `{"status": "pending"}` — keep polling
- `{"status": "complete", "apiKey": "fc-...", "teamName": "..."}` — done

**Step 4 — save the key**

```bash
echo "FIRECRAWL_API_KEY=fc-..." >> .env
```

### Important note

This browser flow is different from `https://www.firecrawl.dev/auth.md`. Use `auth.md` only when the agent platform can mint a WorkOS ID-JAG identity assertion and wants to exchange it directly at `/agent/auth`.

## Path E: Use Firecrawl Without Installing Anything

Use this when you do not want the CLI or skills package. This works for both:

For direct HTTP usage patterns and cURL examples, see `references/rest-api.md`.

- live session-time web work
- application integration via direct REST calls

You still need an API key.

### Base REST details

- **Base URL:** `https://api.firecrawl.dev/v2`
- **Auth header:** `Authorization: Bearer fc-YOUR_API_KEY`

### Key endpoints

- `POST /search` — discover pages by query, optionally with content
- `POST /scrape` — extract clean markdown from one URL
- `POST /interact` — browser actions on live pages
- `POST /support/ask` — diagnose a failing Firecrawl call with `{ question, jobId? }`
- `POST /support/docs-search` — answer Firecrawl documentation questions with citations

### References

- API reference: `https://docs.firecrawl.dev`
- Skills repo: `https://github.com/firecrawl/skills`
- CLI repo: `https://github.com/firecrawl/cli`
- Workflow repo: `https://github.com/firecrawl/firecrawl-workflows`

## Common Pitfalls

1. **Using interact too early.** Start with search or scrape unless the page truly requires clicks, forms, or login.
2. **Guessing after a failed Firecrawl job.** Use `firecrawl ask` with the failing `jobId` instead of inventing recovery steps.
3. **Mixing session tooling with product code.** Path A is for the agent's current session; Path B is for code that will run later in the user's project.
4. **Skipping a smoke test after integration.** Always run one real Firecrawl request after wiring env vars and SDK/API calls.
5. **Repeating browser auth unnecessarily.** Check for an existing valid `FIRECRAWL_API_KEY` before launching the human auth flow again.

## Verification Checklist

- [ ] Firecrawl install command is available and documented exactly
- [ ] The skill cleanly routes among live CLI work, code integration, workflow deliverables, auth, and direct REST use
- [ ] The distinction between Path A and Path B is explicit
- [ ] Install verification commands are included
- [ ] API key handling is called out clearly
- [ ] Support and docs-search recovery paths are included
