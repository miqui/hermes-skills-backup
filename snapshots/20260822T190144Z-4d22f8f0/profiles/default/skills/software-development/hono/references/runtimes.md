# Runtime Getting Started notes

Sources: https://hono.dev/docs/getting-started/<runtime> (cloudflare-workers, deno, bun, nodejs, aws-lambda, vercel, netlify, fastly, service-worker), as published in https://hono.dev/llms-full.txt. The current docs show v5-style `@hono/*` adapter imports; on v4 some adapters are `hono/<runtime>` (see `v5-migration.md`; v5 = release candidate). Verify against the installed version.

All runtimes: scaffold with `npm create hono@latest my-app` (pick the template; also yarn/pnpm/bun/deno equivalents) and test with `await app.request('http://localhost/')`.

## Cloudflare Workers
Source: https://hono.dev/docs/getting-started/cloudflare-workers
- `export default app`; dev on `http://localhost:8787` (`npm run dev`, Wrangler), deploy `npm run deploy`. Port: Wrangler config or CLI options.
- Other handlers (`scheduled`, ...): `export default { fetch: app.fetch, scheduled: async (batch, env) => {} }`.
- Static files: Workers Static Assets, `"assets": { "directory": "public" }` in `wrangler.jsonc`.
- Types: `@cloudflare/workers-types`; or `wrangler types --env-interface CloudflareBindings` and `new Hono<{ Bindings: CloudflareBindings }>()`.
- Bindings via `c.env` (typed with `Bindings`). Testing: `@cloudflare/vitest-pool-workers` recommended.
- `process.env` is not available by default; use `c.env`, or enable `nodejs_compat_populate_process_env` (see the page). Set secrets in Cloudflare config, never in source.
- Middleware that needs env values (e.g. Basic Auth credentials) must be built inside a middleware: `app.use('/auth/*', (c, next) => basicAuth({ username: c.env.USERNAME, password: c.env.PASSWORD })(c, next))`.

## Deno
Source: https://hono.dev/docs/getting-started/deno
- `deno init --npm hono --template=deno my-app`; `Deno.serve(app.fetch)`; `deno task start` (port 8000). Port: `Deno.serve({ port: 8787 }, app.fetch)`.
- Static: `serveStatic` from `@hono/deno` (`deno add jsr:@hono/deno`); options `root`, `path`, `rewriteRequestPath`, `mimes`, `onFound`, `onNotFound`, `precompressed`.
- Tests: `Deno.test` + `@std/assert`, `deno test`. Hono is on npm and JSR (`npm:hono` / `jsr:@hono/hono`).

## Bun
Source: https://hono.dev/docs/getting-started/bun
- `bun create hono@latest my-app`, or `bun add hono` plus `"dev": "bun run --hot src/index.ts"`. `export default app`; `bun run dev` (port 3000).
- Port: `export default { port: 3000, fetch: app.fetch }`. Static: `serveStatic` from `@hono/bun` (same options as Deno). Larger bodies than Bun's default limit also need `maxRequestBodySize` (see body-limit docs).

## Node.js
Source: https://hono.dev/docs/getting-started/nodejs
- Needs the `@hono/node-server` adapter; Node 18.14.1+/19.7.0+/20+. `import { serve } from '@hono/node-server'; serve(app)` (port 3000; `serve({ fetch: app.fetch, port: 8787 })`).
- `serve()` returns the server; close it yourself on SIGINT/SIGTERM.
- WebSocket: built into `@hono/node-server` (`upgradeWebSocket`, `websocket: { server: new WebSocketServer({ noServer: true }) }` with `ws`); `@hono/node-ws` is deprecated.
- Raw Node objects: `c.env.incoming` / `c.env.outgoing` (`HttpBindings` / `Http2Bindings` types).
- Static: `serveStatic` from `@hono/node-server/serve-static`; `root` resolves from `process.cwd()` (use `fileURLToPath(new URL('./', import.meta.url))` for source-relative).
- HTTP/2 via `createServer` (`node:http2`) / `createSecureServer` with `serverOptions` (key/cert read from files; do not commit keys). Docs include a Dockerfile example (non-root user, `node:22-alpine`).

## AWS Lambda
Source: https://hono.dev/docs/getting-started/aws-lambda
- Node.js 18+ runtime; `npm i hono @hono/aws-lambda`; `export const handler = handle(app)`; the docs deploy with AWS CDK (`NodejsFunction`, Function URL).
- Binary responses: set a binary `Content-Type` and Hono base64-encodes `c.body(buffer)`.
- Lambda objects via `c.env`: `Bindings = { event: LambdaEvent; lambdaContext: LambdaContext }`; request context at `c.env.event.requestContext`. (Before v3.10.0 `ApiGatewayRequestContext` binding is deprecated.)
- Response streaming: `streamHandle(app)` from `@hono/aws-lambda` with the Function URL invoke mode changed (see page). The docs' example uses `authType: NONE`; choose real auth for production.

## Vercel
Source: https://hono.dev/docs/getting-started/vercel
- Zero-config: `export default app` from `index.ts`/`src/index.ts`; `vercel dev` (localhost:3000); `vercel deploy`. Needs Vercel CLI. Further: https://vercel.com/docs/frameworks/backend/hono

## Netlify (Edge Functions, Deno)
Source: https://hono.dev/docs/getting-started/netlify
- `netlify/edge-functions/index.ts`: `import { Hono } from 'jsr:@hono/hono'; import { handle } from 'jsr:@hono/netlify'; export default handle(app)`. `netlify dev` (localhost:8888); `netlify deploy --prod`.
- Netlify `Context` via `c.env.context` (`Bindings: { context: Context }`).

## Fastly Compute
Source: https://hono.dev/docs/getting-started/fastly
- `import { fire } from '@fastly/hono-fastly-compute'; fire(app)`; `npm run start` (localhost:7676), `npm run deploy`. Use `Hono` from `'hono'`, not `'hono/quick'`, with top-level `fire`.
- Platform resources (KV, Config/Secret Stores, Backends, ...) via `buildFire({ siteData: 'KVStore:site-data' })` and `Bindings: typeof fire.Bindings`.

## Service Worker
Source: https://hono.dev/docs/getting-started/service-worker
- `npm i hono @hono/service-worker`; in `sw.ts`: `self.addEventListener('fetch', handle(app))` or `fire(app)` (`@hono/service-worker`). Register the worker with `navigator.serviceWorker.register('/sw.ts', { scope: '/sw', type: 'module' })`. The example uses Vite (`vite dev`, port 5173) and `new Hono().basePath('/sw')`.
