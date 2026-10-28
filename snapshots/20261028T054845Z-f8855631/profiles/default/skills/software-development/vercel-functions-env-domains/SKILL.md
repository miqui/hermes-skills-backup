---
name: vercel-functions-env-domains
description: Use when configuring Vercel Functions, cron jobs, env vars, domains, or vercel.json routing. Covers runtimes, Fluid compute, limits, storage via Marketplace, pitfalls.
version: 1.0.0
tags: [vercel, serverless, fluid-compute, cron, env-vars, domains, vercel-json]
---

# Vercel Functions, Env Vars, Domains, Config

Docs fetched 2026-10-28 from https://vercel.com/docs. Limits change; re-check the linked page before asserting a number to a user. Commands not run here are marked UNVERIFIED.

## 1. Functions

**Runtimes (official):** Node.js, Bun, Python (ASGI/WSGI: FastAPI, Flask, Django), Rust, Go, Ruby, plus Edge runtime.
- Fluid compute supports Node.js, Python, Edge, Bun, Rust. Optimized concurrency (many invocations per instance) is Node.js/Python only.
- Fluid is on by default for projects created after 2025-04-23. Older projects: enable in Project Settings > Functions, then redeploy. Per-deployment: `{"fluid": true}` in `vercel.json`.
- Use `waitUntil` (from `@vercel/functions`) for post-response background work.

**Limits (Fluid compute, per docs/functions/limitations):**
| Item | Hobby | Pro / Enterprise |
|---|---|---|
| Max duration default | 300s | 300s |
| Max duration | 300s | 800s (GA) |
| Extended max (Beta) | - | 1800s, per-function config only, Node/Bun/Python |
| Memory default / max | 2 GB, 1 vCPU / same | 2 GB / 4 GB, 2 vCPU |
| Bundle (uncompressed) | 250 MB (Python 500 MB); "large functions" Beta up to 5 GB (needs Fluid + Active CPU) | same |
| Request/response body | 4.5 MB (else 413 FUNCTION_PAYLOAD_TOO_LARGE) | same |
| File descriptors | 1,024 shared across concurrent executions (incl. runtime) | same |
| Concurrency | auto up to 30,000 | 30,000 (Pro), 100,000+ (Ent) |
| Multi-region | no | Pro up to 3; Enterprise all |
- Timeout returns 504 `FUNCTION_INVOCATION_TIMEOUT`.
- Edge runtime: must begin responding within 25s; can stream up to 300s. Edge env vars limited to 5 KB each.
- Node function path: max 128 chars, no spaces.
- Beta >800s: not supported with Secure Compute / Static IPs; no project-level default above 800s.
- Need unbounded time? Use Vercel Workflows, not longer maxDuration.

**maxDuration config**
- Next.js App Router (>=13.5), Node: `export const maxDuration = 60;` in route file.
- Pages router / `api/*.ts`: `export const config = { maxDuration: 60 };`
- SvelteKit/Astro/Nuxt: adapter option (`adapter({ maxDuration: 60 })`; Nuxt `vercel.functions.maxDuration`).
- Python, Go, Ruby, Rust, Next <13.5: `vercel.json`:
```json
{ "functions": { "api/*.py": { "maxDuration": 60 }, "app/main.py": { "maxDuration": 60 } } }
```
  Python frameworks: key on resolved entrypoint (e.g. `app/main.py`).
- Precedence: function code > `vercel.json` > dashboard > Fluid defaults. Glob order in `functions` matters; `**/*` matches everything, prefer `app/api/**/*.ts`.
- Project default: Settings > Functions > Function Max Duration.

**Regions**
- Default `iad1` (Washington DC) for new projects. Co-locate with your database.
- `vercel.json`: `{"regions": ["sfo1"]}`; per function: `"functions": {"api/x.js": {"regions": ["cdg1"]}}`; CLI: `vercel --regions sfo1`.
- `functionFailoverRegions` (project-level, Node): Per-function value is Enterprise only, max 4 regions, fully overrides project value.
- Memory: dashboard (Pro/Ent) sets default memory/CPU; `functions.<glob>.memory` in vercel.json UNVERIFIED this session (check /docs/functions/configuring-functions/memory).

## 2. Cron jobs
```json
{ "crons": [ { "path": "/api/cleanup", "schedule": "0 5 * * *" } ] }
```
- `crons` in `vercel.json` (path + schedule; UTC cron expression). Invokes a Vercel Function via HTTP GET (GET method: UNVERIFIED this session).
- All plans: up to 100 cron jobs per project. Hobby: once per day minimum, timing precision hourly (a `0 1 * * *` may fire 1:00-1:59); a more frequent expression FAILS DEPLOYMENT. Pro/Ent: per-minute.
- Cron usage bills as normal Function usage.
- Secure it: set env var `CRON_SECRET` (random, >=16 chars); Vercel sends it as `Authorization: Bearer <value>` header; compare in the handler and return 401 otherwise.
- Change/delete = edit `vercel.json` and redeploy. "Disable Cron Jobs" (Settings > Cron Jobs) persists across promotions/rollbacks, and disabled jobs still count toward the limit.
- Crons run only on production deployments (UNVERIFIED this session; confirm).
- CLI: `vercel crons` exists (add/list/trigger) per docs index; flags UNVERIFIED.

## 3. Environment variables
- Scopes: team-level (shared) or project-level. Environments: Production, Preview (optionally per-branch override), Development, Custom environments.
- Changes apply only to NEW deployments. Redeploy after editing.
- Types: **Config** (readable after save) and **Secret** (write-only after save; legacy "Sensitive" == Secret). Cannot convert Secret->Config in place (delete and recreate); Secret key can't be edited. Rotate by supplying a new value.
- CLI: `vercel env add NAME production --type secret` (flags per docs `--type config|secret`, `--sensitive`; full syntax UNVERIFIED), `vercel env pull` (writes Development vars to `.env`/`.env.local`), `vercel dev` loads dev vars in-memory.
- Size: 64 KB total per deployment (Node, Python, Ruby, Go); no single var > 64 KB; Edge runtime 5 KB per var.
- Build logs: Secret values >=32 chars appearing in logs are replaced by `[REDACTED]`; `VERCEL_AUTOMATION_BYPASS_SECRET` and `VERCEL_OIDC_TOKEN` always redacted.
- Marketplace integrations inject vars automatically; scope matches the project connection (incl. custom environments).
- System vars (enable "Automatically expose System Environment Variables" in settings; UNVERIFIED location): `VERCEL`, `VERCEL_ENV` (production|preview|development), `VERCEL_TARGET_ENV`, `VERCEL_URL` (no `https://`), `VERCEL_BRANCH_URL`, `VERCEL_PROJECT_PRODUCTION_URL` (always set, even in preview; no scheme), `VERCEL_REGION`, `VERCEL_DEPLOYMENT_ID`, `VERCEL_PROJECT_ID`, `VERCEL_GIT_*` (provider, repo slug/owner, commit ref/sha). `VERCEL_GIT_PREVIOUS_SHA` is build-time and only with an Ignored Build Step.
- Don't use `env`/`build.env` in `vercel.json` (docs recommend against); use Project Settings.
- vercel.json routes can interpolate vars only via explicit `env` whitelist: `{"src":"/api/(.*)","dest":"${BACKEND_URL}/api/$1","env":["BACKEND_URL"]}`.
- Never commit `.env*` pulled files; add to `.gitignore`.

## 4. Domains / DNS
- Domains are owned by a team (Dashboard > Domains) and assigned per project (Project > Settings > Domains). Two separate steps.
- Bought through Vercel: nameservers auto-set, no DNS work. Third-party registrar: either point nameservers to Vercel (then manage records in Vercel DNS) or set records at the registrar as the dashboard instructs (exact records: read from the Domains UI; not asserted here).
- Apex (`acme.com`): Vercel recommends adding a redirect to `www`. Wildcard (`*.acme.com`): MUST use Vercel nameservers (needed for wildcard cert DNS challenge).
- Adding a domain already on another Vercel team requires TXT verification.
- Don't use `alias` in vercel.json (legacy); define domains in Project Settings.
- Email: add MX/TXT records in Vercel DNS if using Vercel nameservers.

## 5. Redirects / rewrites / headers (`vercel.json`)
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "redirects": [ { "source": "/old/:path*", "destination": "/new/:path*", "permanent": true } ],
  "rewrites":  [ { "source": "/api/:path*", "destination": "https://api.example.com/:path*" } ],
  "headers":   [ { "source": "/(.*)", "headers": [ { "key": "X-Frame-Options", "value": "DENY" } ] } ]
}
```
(Shape from general knowledge, not re-fetched this session: UNVERIFIED; confirm at /docs/project-configuration/vercel-json.)
- Redirect changes the URL (308 when `permanent`, else 307); rewrite keeps it. Check order: headers, redirects, then rewrites.
- `routes` (legacy low-level) cannot be mixed with `rewrites/redirects/headers/cleanUrls/trailingSlash` (UNVERIFIED); prefer the newer keys.
- Framework configs (next.config.js) can also define these; don't define the same rule in both.
- Add `"$schema"` for editor validation.

## 6. Storage: current state
- Vercel KV and Vercel Postgres are no longer first-party products. Postgres = Marketplace providers (Neon, Supabase, AWS Aurora Postgres); KV/Redis = Upstash Redis / Redis via Marketplace. NoSQL (MongoDB, DynamoDB) and vector DBs also via Marketplace.
- First-party storage remaining: **Blob** (files; Hobby/Pro, public or private stores) and **Global Config** (ultra-low-latency read-mostly config/flags; all plans).
- Provision: `vercel install neon|upstash|supabase` (installs integration, links to project, pulls creds to `.env.local`; also `vercel integration add`). Credentials arrive as env vars. Run UNVERIFIED here.
- Existing legacy KV/Postgres stores were migrated to Marketplace; migration steps not verified: check the dashboard Storage tab and https://vercel.com/docs/storage.
- Databases: create in the region nearest your function region. Use connection pooling (1,024 FD limit).

## Pitfalls
1. Env var edits don't affect existing deployments: redeploy.
2. Hobby cron more often than daily fails the deploy; timing is +/-59 min.
3. Setting `maxDuration` above plan max is ignored/errors; >800s needs per-function config (Beta, Pro/Ent only).
4. Settings in function code override `vercel.json`, which overrides the dashboard; "why didn't my dashboard change apply?" usually this.
5. 4.5 MB body cap applies to request AND response: use Blob client uploads for large files.
6. Secret vars can't be read back or converted; keep your own source of truth in a password manager.
7. Edge runtime: 5 KB per env var and 25s to first byte.
8. Many DB connections per instance exhaust 1,024 file descriptors: pool and close.
9. Fluid shares process state across concurrent requests: avoid mutable module-level per-request state.
10. Wildcard domains require Vercel nameservers.
11. Cron endpoints are public URLs: always verify `CRON_SECRET`.
12. Tutorials referencing `@vercel/kv` / `@vercel/postgres` are outdated: use provider SDKs.
13. Bytecode caching is production only (Node 20+); preview cold starts are slower.

## Sources (fetched 2026-10-28)
- https://vercel.com/docs/functions/limitations
- https://vercel.com/docs/functions/configuring-functions/duration
- https://vercel.com/docs/functions/configuring-functions/region
- https://vercel.com/docs/functions/runtimes
- https://vercel.com/docs/fluid-compute
- https://vercel.com/docs/cron-jobs/usage-and-pricing
- https://vercel.com/docs/cron-jobs/manage-cron-jobs
- https://vercel.com/docs/environment-variables
- https://vercel.com/docs/environment-variables/sensitive-environment-variables
- https://vercel.com/docs/environment-variables/system-environment-variables
- https://vercel.com/docs/domains/working-with-domains
- https://vercel.com/docs/project-configuration/vercel-json
- https://vercel.com/docs/storage
- https://vercel.com/docs/marketplace-storage
