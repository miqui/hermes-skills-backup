---
name: hono-on-vercel
description: Use when building or deploying a Hono API on Vercel. Covers zero-config entry file, default export, Fluid compute, static assets, middleware, testing, vercel dev, pitfalls.
version: 1.0.0
tags: [hono, vercel, typescript, serverless, fluid-compute, deployment]
---

# Hono on Vercel

Generic Hono topics (routing, middleware API, RPC, JSX, validators): see skill `hono`. This skill covers only the Vercel-specific parts.

## Core rule (current docs)

Vercel deploys Hono with **zero configuration**. No `api/` directory, no `vercel.json`, no `handle()` adapter are needed. Create an entry file that imports `hono` and **default-exports the app**.

Recognized entry locations (the file must import `hono`):

- `app.*`, `index.*`, `server.*` at the project root
- `src/app.*`, `src/index.*`, `src/server.*`
- extensions: js, cjs, mjs, ts, cts, mts

```ts
// src/index.ts
import { Hono } from 'hono'
const app = new Hono()
app.get('/', (c) => c.text('Hello Hono!'))
export default app
```

Server routes automatically become Vercel Functions and run on **Fluid compute** by default.

## Setup

```sh
npm create hono@latest my-app     # pick the `vercel` template
cd my-app && npm i
npm i -g vercel                   # Vercel CLI, needed for vercel dev / deploy
```

Alternative: `vercel init hono` clones Vercel's official Hono example.

## Run and deploy

```sh
vercel dev        # serves on http://localhost:3000, uses the same default export as production
vercel deploy     # preview deployment (add --prod for production)
```

Git integration gives a preview URL per PR.

## Middleware: two different things

- **Hono middleware** (`app.use(logger())`, `cors()`, `basicAuth()`): runs inside Hono's router before handlers. Use for logging, CORS, auth.
- **Vercel Routing Middleware**: runs before the request reaches the app (rewrites, redirects, headers). Separate feature; can be combined with Hono middleware.

## Static assets

- Put files in `public/**`; they are served by Vercel's CDN.
- Hono's `serveStatic()` is **ignored** on Vercel. Do not rely on it.

## Streaming

Vercel Functions support streaming; use Hono's helper:

```ts
import { stream } from 'hono/streaming'
app.get('/stream', (c) =>
  stream(c, async (s) => {
    s.onAbort(() => console.log('Aborted!'))
    await s.write(new Uint8Array([0x48, 0x65, 0x6c, 0x6c, 0x6f]))
  }),
)
```

## Env vars

- Set in the Vercel dashboard or `vercel env add NAME`; pull for local dev with `vercel env pull`.
- Read via `process.env.NAME` (Node runtime, the default). `c.env` is a Cloudflare Workers binding convention; on Vercel it is not populated, so do not use it.
- UNVERIFIED against docs: the fetched pages do not discuss env vars. This follows the general Vercel Node runtime model.

## Zod validation

```ts
import { zValidator } from '@hono/zod-validator'
import { z } from 'zod'
app.post('/echo', zValidator('json', z.object({ name: z.string() })),
  (c) => c.json({ hi: c.req.valid('json').name }))
```

Invalid body returns 400 automatically. Details: see skill `hono`.

## Testing (no server, no Vercel CLI)

Export the app without calling `serve()` and test with `app.request`:

```ts
import app from './src/index'
const res = await app.request('/echo', {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify({ name: 'x' }),
})
// res.status === 200, await res.json() => { hi: 'x' }
```

Verified locally (node 22, hono + zod + @hono/zod-validator + tsx): `GET /` returned 200 `Hello Hono!`, valid POST returned 200 `{"hi":"x"}`, invalid POST returned 400. Run with `npx tsx t.ts`.

## Pitfalls

- **Top-level await with tsx/esbuild**: needs `"type": "module"` in package.json (otherwise esbuild errors with "cjs output format"). Verified.
- **Wrong entry location**: the file must be at one of the listed paths and import `hono`; `api/index.ts` is not in the documented list for the current zero-config flow. If you have a legacy `api/` setup using `hono/vercel` `handle(app)`, that is the older approach and is not covered in the current docs fetched; verify before migrating.
- **No default export**: deployment will not find the app. Always `export default app`.
- **`serveStatic()` silently does nothing**: move files to `public/`.
- **Do not call `serve()` from `@hono/node-server`** in the entry file; Vercel runs the default export.
- **Name collision**: Hono middleware is not Vercel Routing Middleware; configure each in its own place.
- Edge vs Node runtime: the fetched docs state functions use Fluid compute by default and do not describe an edge runtime option for Hono. UNVERIFIED: any `export const runtime = 'edge'` config; check Vercel Functions docs before using.
- `vercel.json` rewrites are not required. UNVERIFIED: custom rewrite syntax was not in the fetched pages; only add if you need it, per Vercel's project configuration docs.
- `vercel dev` and `vercel deploy` need the Vercel CLI and login; UNVERIFIED here (CLI not installed in the test environment).

## Sources (fetched 2026-10-28)

- https://hono.dev/docs/getting-started/vercel
- https://vercel.com/docs/frameworks/backend/hono (last updated Aug 10, 2026)
