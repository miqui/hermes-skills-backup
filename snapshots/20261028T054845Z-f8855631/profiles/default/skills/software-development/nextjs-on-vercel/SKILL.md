---
name: nextjs-on-vercel
description: "Use when deploying or debugging a Next.js App Router app on Vercel. Covers ISR/caching, images, proxy/middleware, Server Actions, runtimes, env vars, monorepos."
version: 1.0.0
tags: [nextjs, vercel, app-router, isr, caching, deployment]
---

# Next.js on Vercel

Current major (per docs fetched 2026-10-28): **Next.js 16**. Min Node 20.9, TypeScript 5.1, Turbopack default for `next dev`/`next build`. Verify the installed version first (`npm ls next`) and read the matching docs in `node_modules/next/dist/docs/` (16.2+) before trusting memory.

## Deploy (App Router)
- Zero-config: Vercel auto-detects Next.js. Git import (preferred) or CLI: `npm i -g vercel && vercel` (preview), `vercel --prod` (production). UNVERIFIED (not run).
- Every PR/branch push gets a **preview deployment** URL; production = production branch. Pull env vars locally: `vercel env pull .env.local` (UNVERIFIED).
- Build settings (framework preset, build command, Node version) live in Project Settings; override in `vercel.json` only when needed.
- Next 16 + custom `webpack` config: `next build` fails by default. Use `--webpack` to keep it, or migrate to Turbopack config.

## Middleware → Proxy rename (Next 16)
- `middleware.ts` is now **`proxy.ts`**; export `proxy` (named or default) instead of `middleware`. Same functionality, one file per project, at project root or `src/`, same level as `app`.
- Codemod: `npx @next/codemod@canary upgrade latest` (UNVERIFIED; handles the rename, `unstable_` removal, `next lint` migration).
- Use for rewrites, redirects, header changes, optimistic auth checks. NOT for slow data fetching or sole authorization — re-check auth in Server Actions/Route Handlers/data layer.
- `fetch` cache options (`cache`, `next.revalidate`, `next.tags`) have no effect in Proxy.
- Prefer `redirects`/`rewrites` in `next.config.ts` for simple static cases.
- Runtime: Proxy runs on Node.js in 16 (one third-party source claims Edge needs explicit opt-in and that matcher semantics changed — UNVERIFIED, test your matcher on a preview deployment). Next 15 and earlier keep `middleware.ts` (Edge default).

```ts
// proxy.ts
import { NextResponse, type NextRequest } from 'next/server'
export function proxy(request: NextRequest) {
  return NextResponse.next()
}
export const config = { matcher: ['/((?!api|_next/static|_next/image|.*\\..*).*)'] }
```

## Caching, ISR, revalidation
- Vercel supports ISR: pages/data regenerate in the background without redeploy; served from the CDN.
- Time-based: `export const revalidate = 60` (segment) or `fetch(url, { next: { revalidate: 60, tags: ['posts'] } })`.
- On-demand: `revalidatePath('/blog')`, `revalidateTag('posts', 'max')`.
  - **Next 16:** `revalidateTag` needs a 2nd arg (a `cacheLife` profile, e.g. `'max'`); single-arg is deprecated/TS error. It is stale-while-revalidate.
  - **`updateTag('posts')`** (Server Actions only): immediate expiry, read-your-writes after a mutation.
- Cache Components (`cacheComponents: true` in `next.config.ts`, `'use cache'`, `cacheLife`, `cacheTag`) is opt-in in 16 and replaces `experimental_ppr`. Do not enable just to finish an upgrade.
- Reading `cookies()`, `headers()`, `searchParams`, or using `dynamic = 'force-dynamic'` makes a route dynamic (no ISR). In 16 these Request APIs are async: `await cookies()`, `await params`.
- Verify caching with response header `x-vercel-cache` (HIT/MISS/STALE/PRERENDER) on a deployed URL, not `next dev`.
- `generateStaticParams` pre-renders known paths; unknown params render on demand then cache (control with `dynamicParams`).

## Image Optimization
- Use `next/image`. Vercel's optimizer is automatic; no loader config required.
- Remote images must be allowed: `images.remotePatterns: [{ protocol: 'https', hostname: 'cdn.example.com' }]` (avoid deprecated `domains`).
- Next 16 changes: `minimumCacheTTL` default raised; local images with query strings need `images.localPatterns`; check `images.qualities`. Read the version-16 upgrade guide before tuning.
- Set `width`/`height` or `fill` + `sizes` to avoid layout shift and oversized variants. Use `priority` only for the LCP image.
- Cost: transformations/cache writes are metered; prefer static imports and sane `sizes`. Large video/GIF → don't serve through the optimizer.

## Server Actions
- `'use server'` functions invoked via forms/`action`; run as server functions on Vercel (billed as function invocations).
- Always validate input and authorize inside the action — they are public POST endpoints.
- After mutating: `updateTag`/`revalidatePath`/`revalidateTag` then `redirect()` (redirect throws; call it outside `try/catch`).
- Body size limit default 1MB; change via `experimental.serverActions.bodySizeLimit`. Vercel function payload limit (4.5MB) still applies — use direct-to-Blob uploads for large files.
- Self-hosted/multi-deploy encryption key: set `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` if closures must survive across builds (UNVERIFIED for your setup).

## Route Handlers
- `app/api/x/route.ts` exporting `GET`/`POST`/etc. `GET` handlers are not cached by default in 15+; opt in with `export const dynamic = 'force-static'` or `revalidate`.
- Use Web `Request`/`Response`; `await` params: `(req, { params }: { params: Promise<{id:string}> })`.
- Set `export const maxDuration = 30` for long work (limit depends on plan); stream for long responses.
- Do not call your own Route Handler from a Server Component — call the shared function directly.

## Node vs Edge runtime
- Default is Node.js (`export const runtime = 'nodejs'`). Use it unless you have a reason.
- Edge (`export const runtime = 'edge'`): Web APIs only, no most Node built-ins/native modules, small bundle limit. Lower cold start; choose for simple low-latency handlers.
- Fluid compute / region: set function region near your database (`preferredRegion` / project Settings → Functions) to cut DB latency.
- Proxy (16) is Node-based; do not assume Edge there.

## Environment variables
- Set in Project Settings → Environment Variables, scoped per Production/Preview/Development (and per-branch for Preview). Changes apply only to **new** deployments — redeploy.
- `NEXT_PUBLIC_*` is **inlined into the client bundle at build time**: visible to everyone, never put secrets in it, and changing it needs a rebuild. Non-prefixed vars are server-only.
- Read dynamic server values at request time (e.g. `process.env.X` inside a handler), not at module top-level if it must differ per deploy env.
- System vars: `VERCEL_ENV` (`production|preview|development`), `VERCEL_URL` (no protocol), `VERCEL_GIT_COMMIT_REF`. Expose to client via `NEXT_PUBLIC_VERCEL_ENV` (enable "Automatically expose System Environment Variables").
- Local: `.env.local` (gitignored); never commit secrets.

## Speed Insights & Analytics
- `npm i @vercel/analytics @vercel/speed-insights`; add `<Analytics />` (`@vercel/analytics/next`) and `<SpeedInsights />` (`@vercel/speed-insights/next`) to `app/layout.tsx` body. UNVERIFIED (not run).
- Enable each in the Vercel dashboard (project → Analytics / Speed Insights) first, then redeploy. Data appears only on deployed traffic, not localhost; ad blockers drop events.

## Preview deployments
- One per push/PR; unique URL + stable branch URL. Preview-scoped env vars apply.
- Deployment Protection (Vercel Auth) is on by default for previews: external webhooks/crawlers get 401 — use a protection bypass secret or adjust the setting.
- OAuth/webhook callback URLs differ per preview; avoid hardcoding the production domain (use `VERCEL_URL`/relative paths).
- Don't use `robots` indexing on previews; Vercel sends `X-Robots-Tag: noindex` for them.

## Monorepos / Root Directory
- Create one Vercel Project per app; set **Root Directory** (Project Settings → Build and Deployment) to e.g. `apps/web`.
- Enable "Include source files outside of the Root Directory" when importing workspace packages (default on for new projects).
- Run `vercel` / `vercel link` from the **monorepo root**, not the subdirectory.
- Install at repo root (pnpm/npm/yarn workspaces); with Turborepo, Vercel auto-detects and uses remote cache. Skip unaffected projects via "Ignored Build Step" or Turborepo's affected detection.
- Cross-project URLs: `relatedProjects` in `vercel.json` + `@vercel/related-projects`.
- Transpile local TS packages with `transpilePackages: ['@acme/ui']` in `next.config.ts`.

## Pitfalls
- Following Next 15 tutorials on 16: `middleware.ts` still works but is deprecated; sync `params`/`cookies()` break; `revalidateTag` one-arg errors.
- Testing caching/ISR with `next dev` — it never caches; check deployed `x-vercel-cache`.
- Secrets in `NEXT_PUBLIC_*`; env var edits not applied until redeploy.
- Relying on Proxy for auth only (bypassable via direct Server Action/handler calls).
- Unlisted remote image host → 400 from `/_next/image`.
- Using `fs` writes at runtime: filesystem is read-only/ephemeral on Vercel (only `/tmp`); use a DB/Blob.
- Function timeout/payload limits (4.5MB request body); heavy work → background (`after()`/queues).
- Wrong Root Directory in monorepos → "No Next.js version detected" build error.
- Case-sensitive imports pass on macOS, fail on Vercel's Linux build.
- Turbopack default + custom webpack config = failing build.

## Sources (fetched 2026-10-28)
- https://vercel.com/docs/frameworks/full-stack/nextjs
- https://vercel.com/docs/monorepos
- https://nextjs.org/docs/app/getting-started/proxy
- https://nextjs.org/docs/app/guides/upgrading/version-16
- Proxy runtime/matcher claims come from an unofficial source (unverified).

Note: sections on Server Actions limits, Route Handler defaults, runtimes, env vars, Analytics, previews were written from prior knowledge plus partially-fetched docs; confirm specifics (limits, flags) against current docs before relying on them.
