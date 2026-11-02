---
name: nextjs
description: Use when building, debugging, reviewing, testing, or deploying Next.js App Router apps (Server/Client Components, caching, Server Actions, route handlers, proxy).
version: '1.0'
metadata:
  hermes:
    tags: [nextjs, react, typescript, app-router, server-components, frontend, fullstack]
    related_skills: [node-backend, typescript, playwright-testing, hono, application-authorization]
---

# Next.js (App Router)

## Overview
Full-stack React framework. This skill targets the **App Router** on **Next.js 16.x**.
Verified against nextjs.org/docs: the version guides list 16/15/14 as latest, and `proxy.js` history shows
`v16.0.0` renamed Middleware to Proxy. The exact latest minor (e.g. 16.x) is UNVERIFIED; docs pages were dated Oct 2026.
Always check the installed version (`node_modules/next/package.json`) and the bundled docs at
`node_modules/next/dist/docs/` (docs say upgrades update these) before relying on this skill.
Scaffolds from `create-next-app` also include `AGENTS.md`; read it if present.

## When to use
- Creating, modifying, debugging, reviewing, testing or deploying a Next.js App Router project.
- Not for standalone backend APIs: see node-backend and hono.
- Pages Router (`pages/`) is a different model; not covered here.

## Setup
- Requires Node.js >= 20.9. https://nextjs.org/docs/app/getting-started/installation
- `pnpm create next-app@latest my-app --yes` (defaults: TypeScript, Tailwind, ESLint, App Router, Turbopack, `@/*` alias, AGENTS.md; recommended prompt defaults also list Cache Components).
- Scripts: `next dev`, `next build`, `next start`, `eslint`.
- Turbopack is the default bundler; use `--webpack` flag on dev/build to opt out.
- Upgrade: `pnpm next upgrade` (16.1.0+; earlier versions need a separate package). Guide: https://nextjs.org/docs/app/getting-started/upgrading

## Project structure
Docs: https://nextjs.org/docs/app/getting-started/project-structure
- `app/` routes by folder; `page.tsx` makes a route public; `layout.tsx` wraps children; `loading.tsx` (Suspense fallback); `error.tsx`; `not-found.tsx`; `route.ts` for route handlers.
- Optional `src/` directory; `public/` for static assets.
- `proxy.ts` at project root (or inside `src`, level with `app`).
- `next.config.ts` typed as `NextConfig`.
- Private folders `_name`, route groups `(name)`, dynamic `[slug]`, parallel `@slot` exist (details UNVERIFIED in this pass; see project-structure page).

## Server vs Client Components
Docs: https://nextjs.org/docs/app/getting-started/server-and-client-components (not fetched; summary from general knowledge, UNVERIFIED in detail)
- Components in `app/` are Server Components by default: can be `async`, access DB/secrets, add nothing to client bundle.
- Add `'use client'` at top of a file for state, effects, event handlers, browser APIs. It marks a boundary: imports below become client code.
- Keep client boundaries small/leaf-level; pass Server Components as `children` into Client Components.
- Props crossing the boundary must be serializable.
- Never import server-only secrets into client files; use the `server-only` package (UNVERIFIED) to guard modules.

## Data fetching
Docs: https://nextjs.org/docs/app/getting-started/fetching-data (verified)
- Server Components: make the component `async` and `await fetch(...)` or an ORM/DB call directly.
- Identical `fetch` requests in one render tree are memoized.
- `fetch` is NOT cached by default; it blocks rendering until complete. Either cache with `use cache` or wrap the component in `<Suspense>` to stream.
- Still authenticate/authorize in data access: https://nextjs.org/docs/app/guides/data-security
- Client Components: fetch via React `use` with a promise from a Server Component, or a library like SWR/React Query (the latter UNVERIFIED on this page).

## Caching (Cache Components model)
Docs: https://nextjs.org/docs/app/getting-started/caching and https://nextjs.org/docs/app/getting-started/revalidating
- Enabled with `cacheComponents: true` in `next.config.ts`; also set `partialPrefetching` explicitly (unset logs a warning; `false` only while migrating).
  New apps from recommended `create-next-app` defaults already have both.
- `'use cache'` directive caches async functions or components (data-level or UI-level). Pair with `cacheLife('hours')` etc. from `next/cache`; without it the implicit `default` profile applies.
- Arguments and captured values become the cache key.
- Uncached/runtime data should sit inside `<Suspense>` so the static shell prerenders and dynamic parts stream.
- With Cache Components, `GET` route handlers follow the same prerender model as pages.
- On-demand revalidation after mutations: see revalidating page (`revalidateTag`, `revalidatePath`, `updateTag`: names UNVERIFIED here; confirm signatures in docs).
- Without Cache Components, the older model applies (route segment config, `fetch` cache options): https://nextjs.org/docs/app/guides/caching-without-cache-components
- Request-time APIs `cookies()`, `headers()`, `params`, `searchParams` are async in 15+ (`await` them); UNVERIFIED on a fetched page this pass.

## Route handlers & Server Actions
Route handlers: `app/**/route.ts` exporting `GET`/`POST`/etc. using Web `Request`/`Response`. https://nextjs.org/docs/app/getting-started/route-handlers (not fetched; only the Cache Components link was verified).

Server Functions/Actions: https://nextjs.org/docs/app/getting-started/mutating-data (verified)
- Async function with `'use server'` (inline in a Server Component, or at top of a file to mark all exports).
- Cannot be defined inside Client Components; import them from a `'use server'` file.
- Used via `<form action={fn}>` or `<button formAction={fn}>`; forms progressively enhance in Server Components.
- Next.js can return updated UI and data in a single roundtrip. Actions use POST only.
- WARNING: reachable by direct POST. Verify authn/authz inside EVERY Server Function.
- More: https://nextjs.org/docs/app/guides/server-actions

## Proxy (formerly middleware)
Docs: https://nextjs.org/docs/app/api-reference/file-conventions/proxy (verified)
- `middleware` is deprecated; rename file to `proxy.ts` and function to `proxy` (or default export). Single function per file.
- Defaults to Node.js runtime from v16.0.0.
- Runs before routes render: redirects, rewrites, header/cookie changes, early responses.
- Without `config.matcher` it runs on EVERY request, including `_next/static`, `_next/image`, `public/`. Use a negative matcher, e.g. `'/((?!api|_next/static|_next/image|.*\\.png$).*)'`.
- Do not rely on shared modules/globals; pass data via headers, cookies, rewrites, redirects, or URL.
- Treat as a coarse gate, not the only auth check (see auth).

## Auth pointers
- Check auth at the data access layer and in each Server Action/route handler, not only in proxy. https://nextjs.org/docs/app/guides/data-security
- Next.js authentication guide: https://nextjs.org/docs/app/guides/authentication (not fetched; UNVERIFIED).
- `forbidden()`/`unauthorized()` and `authInterrupts` were listed as canary-only on the upgrading page; confirm before use.
- Authorization design patterns: use skill application-authorization.

## Environment variables
Docs: https://nextjs.org/docs/app/guides/environment-variables (not fetched; UNVERIFIED)
- `.env`, `.env.local`, `.env.development`, `.env.production` loaded automatically; do not commit `.env.local`.
- Only `NEXT_PUBLIC_*` vars are inlined into the client bundle at build time; everything else stays server-side.
- Build-time inlining means changing a `NEXT_PUBLIC_` value requires a rebuild.

## Testing
- E2E: Playwright. https://nextjs.org/docs/app/guides/testing/playwright (verified): `pnpm create playwright`, configure `webServer` in `playwright.config.ts`; the doc suggests testing against a production build (`next build && next start`) (UNVERIFIED which section). See skill **playwright-testing**.
- With Cache Components, `instant()` from `@next/playwright` asserts what is visible right after navigation before dynamic content streams.
- Unit: Jest/Vitest guides exist at /docs/app/guides/testing/jest and /vitest. Note async Server Components are poorly supported by unit runners (UNVERIFIED); prefer E2E for them.

## Deployment
Docs: https://nextjs.org/docs/app/getting-started/deploying (verified)
- Node.js server (`next build` + `next start`): all features.
- Docker: all features; `output: 'standalone'` for minimal images (example in vercel/next.js `examples/with-docker`).
- Static export (`output: 'export'`): limited features.
- Adapters for other platforms: feature support varies. https://nextjs.org/docs/app/guides/deploying-to-platforms
- Self-hosting config: https://nextjs.org/docs/app/guides/self-hosting
- Streaming behind proxies/CDNs and bots/crawlers: https://nextjs.org/docs/app/guides/streaming

## Common pitfalls
- Adding `'use client'` too high, shipping whole trees to the browser.
- Assuming `fetch` is cached; it is not by default (verified).
- Forgetting `Suspense` around uncached/runtime data when Cache Components is on, causing blocked or errored prerender.
- Proxy without `matcher` blocking static assets (verified).
- Still using `middleware.ts`: deprecated since v16 (verified).
- Trusting UI-only auth: Server Actions are public POST endpoints (verified).
- Data sources missing at request time that exist at build-time prerender can make bots get 500s (see caching page).
- Using `NEXT_PUBLIC_` for secrets (UNVERIFIED page, widely documented).
- Following old tutorials with synchronous `params`/`cookies()` or Pages Router APIs; check installed version.
- Webpack-only plugins/config under Turbopack default; use `--webpack` if needed.

## See also
- node-backend, hono: standalone backend APIs not tied to React rendering.
- typescript, playwright-testing, application-authorization.
- Docs index: https://nextjs.org/docs/app
