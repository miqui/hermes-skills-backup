---
name: hono
description: Use when building, testing, reviewing, or debugging Hono applications, including Hono routing, middleware, request validation, JSX, streaming, WebSockets, typed RPC clients, runtime adapters, and v4-to-v5 migration.
metadata:
  version: '1.2'
  hermes:
    tags: [hono, typescript, web-framework, routing, middleware, cloudflare-workers, edge]
    related_skills: [node-backend, typescript, cloudflare-workers, bun-backend, nextjs]
---

# Hono

## Overview

Hono is a TypeScript web framework built on Web Standards that runs on Cloudflare Workers, Deno, Bun, Node.js, and other runtimes. Use this skill for application behavior and framework patterns; pair it with the runtime-specific skill when platform bindings, deployment configuration, or runtime limits matter.

## When to Use

- Code imports from `hono` or `hono/*`.
- Building or reviewing Hono routes, middleware, request handling, validation, rendering, streaming, WebSockets, or RPC clients.
- Working with Hono on Cloudflare Workers, Node.js, Bun, Deno, AWS Lambda, Vercel, Netlify, or Fastly.
- Testing an app through `app.request()` or `testClient()` without first starting an HTTP server.

Do not use this skill as the source of truth for a runtime's deployment configuration, bindings, or limits. For Cloudflare Workers-specific lifecycle and binding behavior, also load `cloudflare-workers`.

## Documentation and Version Grounding

- Start with the official Hono documentation (https://hono.dev/docs; the whole site is at https://hono.dev/llms-full.txt). For behavior that depends on a package version, verify the project's lockfile plus installed types or source before changing code.
- Treat local project conventions and existing app composition as authoritative unless they conflict with Hono's documented API.
- Check the runtime adapter's documentation before assuming an API works identically on Workers, Node.js, Bun, or Deno.
- The bare `hono` binary exists only when `@hono/cli` is installed (`npm i -D @hono/cli`, or globally). It then provides `hono request`, `hono batch`, `hono routes`, `hono snapshot`, and `hono diff` (JSON output, no server needed). Without `@hono/cli`, do not assume `npx hono ...` works; fall back to `app.request()` and `testClient()`. See `references/helpers.md` (CLI section).

## Version Notes: v4 vs v5

Hono v5 is a **release candidate** (`npm install hono@next`); the docs site already describes v5 behavior in places. **Verify the installed version** (`package.json`, lockfile, `node_modules/hono/package.json`) before applying either set of rules. Full list: `references/v5-migration.md`.

| Area | v4 | v5 (release candidate) |
| --- | --- | --- |
| `onError` | `app.onError((err, c) => ...)` | `app.onError((c) => ...)`, read `c.error` |
| `c.req.json()` | `Promise<any>` | `Promise<unknown>`; pass a type or use `c.req.valid()` |
| `c.req.query()` (no key) | `string` values | `string \| undefined` values |
| `c.json(undefined)` | empty body | throws `TypeError` |
| Runtime adapters | `hono/bun`, `hono/deno`, `hono/cloudflare-workers`, `hono/aws-lambda`, `hono/lambda-edge`, `hono/netlify`, `hono/vercel`, `hono/service-worker` | `@hono/bun`, `@hono/deno`, `@hono/cloudflare-workers`, `@hono/aws-lambda`, `@hono/lambda-edge`, `@hono/netlify`, `@hono/vercel`, `@hono/service-worker` |
| `hono/cloudflare-pages` | present | removed (use Workers with static assets) |
| `app.mount()` | works (deprecated) | removed -> `mount` from `hono/mount` |
| `app.fire()` | works (deprecated) | removed -> `fire(app)` from `@hono/service-worker` |
| `c.req.routePath` / `c.req.matchedRoutes` | works (deprecated) | removed -> `routePath(c)` / `matchedRoutes(c)` from `hono/route` |

`hono/adapter` (`env()`, `getRuntimeKey()`) stays in `hono`. v5 is ESM-only; `require('hono')` needs Node.js 22.12+.

## App, Routing, and Errors

Use a typed environment when bindings or request-scoped variables are involved:

```ts
import { Hono } from 'hono'

type Env = {
  Bindings: { DATABASE: D1Database }
  Variables: { user: { id: string; name: string } }
}

const app = new Hono<Env>()

app.get('/users/:id', (c) => c.json({ id: c.req.param('id') }))
app.get('/posts/:id{[0-9]+}', (c) => c.text(c.req.param('id')))

app.notFound((c) => c.json({ message: 'Not Found' }, 404))
app.onError((err, c) => { // v4 signature; v5 RC: app.onError((c) => ... c.error)
  console.error(err)
  return c.json({ message: 'Internal Server Error' }, 500)
})
```

- Register routes and middleware in deliberate order. Handlers and middleware run in registration order, and a handler that returns stops processing: put specific routes before broad parameter or wildcard routes, middleware above the handlers it wraps, and fallbacks (`app.get('*', ...)`) last.
- Use `app.route('/api', api)` to mount a feature sub-app, or `new Hono().basePath('/api')` for a scoped app. `route()` copies the sub-app's routes at call time, so register nested routes first: `two.route('/three', three)` *before* `app.route('/two', two)`; the wrong order returns 404.
- HEAD requests are converted to GET before route matching, so `app.head()` / `app.on('HEAD', ...)` handlers never run. Use the GET route, or middleware that checks `c.req.method === 'HEAD'`.
- Strict mode is on by default: `/hello` and `/hello/` are different. `new Hono({ strict: false })` treats them the same.
- Optional param: `/api/animal/:type?`. Regexp param: `/post/:date{[0-9]+}`. A param containing slashes needs a regexp such as `:filename{.+\\.png}`.
- `app.notFound()` is only called from the top-level app; a `notFound` set on a sub-app is not used. If a parent and a route both define `onError`, the route-level handler wins.
- Throw `HTTPException` for deliberate error responses (`import { HTTPException } from 'hono/http-exception'`): `throw new HTTPException(401, { message: 'Unauthorized' })`, or `{ res: new Response(...) }` for a custom response, plus optional `cause`. In `onError`, `if (err instanceof HTTPException) return err.getResponse()`. `getResponse()` is not Context-aware: headers set earlier with `c.header()` are lost, so copy them onto the new `Response`.
- Return `c.json()`, `c.text()`, `c.html()`, `c.redirect()`, `c.body()`, or a `Response`; do not leave a handler without a response.
- Keep handlers inline after the path (`app.get('/books/:id', (c) => ...)`) so path params are inferred. Do not build Rails-style controller functions typed with a bare `Context`; if separate handlers are really needed, use `factory.createHandlers()` from `hono/factory` (see `references/helpers.md`). Split a large app into files with `app.route()`.

## Context and Request Data

```ts
app.post('/posts/:id', async (c) => {
  const id = c.req.param('id')
  const page = c.req.query('page')
  const tags = c.req.queries('tag')
  const payload = await c.req.json()

  c.header('Cache-Control', 'no-store')
  c.status(201)
  return c.json({ id, page, tags, payload })
})
```

- Use `c.req.param()`, `query()`, `queries()`, and `header()` for URL and header inputs. `c.req.header()` with no argument returns a record whose keys are all **lowercase**; read `c.req.header('X-Foo')` for a named header.
- Parse each body once with the appropriate method: `json()`, `text()`, `formData()`, `parseBody()`, `arrayBuffer()`, or `blob()`.
- Pass request-scoped values through `c.set('key', value)` and retrieve them with `c.var.key` or `c.get('key')`; do not use module-global mutable request state.
- After `await next()`, `c.error` holds an error thrown by a handler (check it in middleware), and `c.res` can be read or replaced (`c.res = new Response('New')`).
- On Workers, access bindings through `c.env` and request-lifetime work through `c.executionCtx`. `process.env` is not available on Workers by default; read configuration from `c.env`. Follow runtime-specific lifecycle guidance for `waitUntil()` and WebSockets.

## Middleware and Typed Variables

Middleware is onion-style: registration order controls the request path, and code after `await next()` runs while unwinding the response path.

```ts
import { createMiddleware } from 'hono/factory'

const requireUser = createMiddleware<Env>(async (c, next) => {
  const token = c.req.header('Authorization')
  if (!token) return c.json({ error: 'Unauthorized' }, 401)

  c.set('user', { id: 'user_123', name: 'Ada' })
  await next()
})

app.use('/api/*', requireUser)
```

- Middleware that continues must `await next()`. Middleware that rejects, redirects, or otherwise completes the request must return its response instead.
- Put resource setup before authentication, and authentication before protected routes.
- Register CORS before the routes it protects (and before authentication when credentialed cross-origin requests need preflight handling); keep the CORS policy narrowly scoped.
- Use built-in middleware such as `cors`, `logger`, `secureHeaders`, `csrf`, `bearerAuth`, or `jwt` only where their behavior matches the route and deployment model. Catalog: `references/middleware-catalog.md`.
- Use `createFactory<Env>()` when an app, middleware, and separately defined handlers need the same `Env` type.
- Chained `.use()` calls accumulate `Variables` types, so handlers after `new Hono().use(auth).use(db).get(...)` see both without a hand-written combined `Env`.
- Middleware factories that need environment secrets (`jwt`, `basicAuth`, `cors` with env origins) must be created inside a middleware so they can read `c.env`: `app.use('/auth/*', (c, next) => jwt({ secret: c.env.JWT_SECRET, alg: 'HS256' })(c, next))`.
- `upgradeWebSocket()` changes response headers internally. Header-modifying middleware (for example CORS) on a WebSocket route can fail with "immutable headers"; keep upgrade detection explicit and skip such middleware there.

## Security Defaults

- **CSRF** (`hono/csrf`): checks `Origin` and `Sec-Fetch-Site` (allowed if either passes) and only validates unsafe methods (not GET/HEAD/OPTIONS) sent with form content types (`application/x-www-form-urlencoded`, `multipart/form-data`, `text/plain`). A JSON POST is not covered by it. For a function-valued `origin`, anchor regexes with `$` and never forward-match (`/https:\/\/(\w+\.)?myapp\.example\.com$/`).
- **JWT** (`hono/jwt`): `alg` is required alongside `secret`; read the verified payload with `c.get('jwtPayload')`. Set `verification.iss` / `aud` when issuer or audience matters (`iss` is not checked unless set).
- **JWK** (`hono/jwk`): rejects `HS256/384/512`; configure an asymmetric `alg` allowlist and keys or `jwks_uri`.
- **Body size** (`hono/body-limit`): default `maxSize` is 100KB (`100 * 1024`). On Bun, larger limits also need `maxRequestBodySize` in the Bun server config.
- **CORS**: install before routes; list explicit origins.
- **Secrets**: the official docs show literal secrets (`'it-is-very-secret'`, basic-auth passwords) in examples. Never copy them. Read secrets from `c.env` (Workers) or `process.env` (Node/Bun/Deno) and keep real values out of source, tests, and command arguments.

## Validation

Validate each untrusted request part before using it. Targets are `json`, `form`, `query`, `header`, `param`, and `cookie`; multiple validators can sit on the same route.

```ts
import { zValidator } from '@hono/zod-validator'
import { z } from 'zod'

const createPost = z.object({
  title: z.string().min(1),
  body: z.string(),
})

app.post('/posts', zValidator('json', createPost), (c) => {
  const post = c.req.valid('json')
  return c.json(post, 201)
})
```

- Use `c.req.valid(<target>)` only after the matching validator has run.
- `json` and `form` validators require a matching `Content-Type` request header; otherwise the body is not parsed and the validator sees `{}`. This also applies to `app.request()` tests: pass `headers: { 'Content-Type': 'application/json' }`.
- `header` validation keys must be **lowercase** (`value['idempotency-key']`, not `value['Idempotency-Key']`).
- `@hono/standard-validator` (`sValidator`) is appropriate when the project uses a Standard Schema-compatible library such as Valibot or ArkType; do not introduce a second validation ecosystem without a project-level reason.
- Return a safe validation error and avoid parsing the same body separately in downstream middleware or handlers.
- OpenAPI generation from Zod schemas (`@hono/zod-openapi`, not on hono.dev): `references/openapi-zod.md`.

## JSX and Rendering

Files containing JSX must use `.tsx` and require the Hono JSX runtime:

```json
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "jsxImportSource": "hono/jsx"
  }
}
```

```tsx
import type { PropsWithChildren } from 'hono/jsx'

const Layout = ({ children }: PropsWithChildren) => (
  <html><body>{children}</body></html>
)

app.get('/', (c) => c.html(<Layout><h1>Hello</h1></Layout>))
```

Use a renderer or `jsxRenderer` for shared layouts. Keep async data access inside async components or handlers, and render escaped values through JSX rather than interpolating untrusted strings as raw HTML. More (Deno config, metadata hoisting, `hono/jsx/dom`): `references/jsx.md`.

## Streaming, SSE, and WebSockets

```ts
import { streamSSE } from 'hono/streaming'

app.get('/events', (c) => streamSSE(c, async (stream) => {
  stream.onAbort(() => console.info('SSE client disconnected'))
  await stream.writeSSE({ event: 'ready', data: JSON.stringify({ ok: true }) })
}))
```

- Use `stream`, `streamText`, or `streamSSE` for streaming responses rather than buffering a large result in memory.
- Handle abort/disconnect events and bound long-running loops; do not leave an unbounded producer running after the client has gone away.
- WebSocket upgrades require the runtime's matching adapter (Node.js: `upgradeWebSocket` from `@hono/node-server` plus `ws`; `@hono/node-ws` is deprecated). Keep connection ownership and lifecycle rules runtime-specific.

## Testing Without a Server

Prefer direct request tests before starting a network server:

```ts
const response = await app.request('/posts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ title: 'Hello', body: 'World' }),
})

expect(response.status).toBe(201)
expect(await response.json()).toEqual({ title: 'Hello', body: 'World' })
```

- Pass a `Request` object to `app.request()` when the test needs an exact URL or method.
- Supply mock bindings as the third `app.request()` argument for Worker-oriented behavior; do not require real cloud services in unit tests.
- Use `testClient(app)` for typed route calls when the routes are defined through chained Hono methods.
- Test middleware rejection, validation failures, not-found behavior, and error mapping—not only successful handlers. For HEAD, assert it matches GET status and headers with a null body.

## Type-Safe RPC Clients

Route chaining preserves route types for Hono's client and testing helpers:

```ts
const routes = app
  .post('/posts', zValidator('json', createPost), (c) => c.json({ ok: true }, 201))
  .get('/posts', (c) => c.json({ posts: [] }))

export type AppType = typeof routes
```

```ts
import { hc } from 'hono/client'
import type { AppType } from './server'

const client = hc<AppType>('http://localhost:8787/')
const response = await client.posts.$post({ json: { title: 'Hello', body: 'World' } })
```

- Define the typed route chain directly on the Hono instance and export the resulting type.
- Use `InferRequestType` and `InferResponseType` only where a shared type is genuinely clearer than deriving it from the route call.
- Keep server and client package versions compatible; type inference problems are often caused by split or duplicate Hono versions. Set `"strict": true` in both tsconfig files. More: `references/rpc.md`.

## Runtime Adapters and Routers

```ts
// Cloudflare Workers or Bun (Bun: { port, fetch: app.fetch } to set the port)
export default app

// Deno
Deno.serve(app.fetch)

// Node.js
import { serve } from '@hono/node-server'
serve(app)
```

- Install and use the adapter that matches the actual runtime; do not assume the default export starts a Node HTTP server. Per-runtime setup: `references/runtimes.md`.
- Keep framework logic portable, but isolate runtime bindings, upgrade handling, and deployment configuration at the adapter boundary.
- Routers: the default `hono` preset uses `SmartRouter[RegExpRouter, TrieRouter]`; `hono/quick` (`SmartRouter[LinearRouter, TrieRouter]`) suits per-request initialization; `hono/tiny` (`PatternRouter`) is the smallest. All export the same `Hono` class. Details: `references/routers-presets.md`.

## Common Pitfalls

1. **Registering a broad route before a specific route.** Hono uses registration order; move the specific route first.
2. **Calling `await c.req.json()` more than once.** Parse once, validate once, and pass the typed result forward.
3. **Using `c.req.valid()` without matching validator middleware.** Add and order the validator before the handler.
4. **Losing RPC or `testClient` inference.** Chain the route declarations and export the type of the chain.
5. **Putting JSX in a `.ts` file.** Rename it to `.tsx` and set `jsxImportSource` to `hono/jsx`.
6. **Testing only through a live server.** Start with `app.request()` plus mock bindings for fast, deterministic tests.
7. **Hardcoding credentials in authentication middleware.** Obtain them from the runtime's approved configuration or secret store; never place real credentials in source, tests, or command arguments.
8. **Treating Workers and Node as interchangeable.** Verify adapter, bindings, WebSocket, and lifecycle behavior for the deployed runtime.
9. **Missing `Content-Type` in validator tests.** `json`/`form` validators otherwise see an empty object.
10. **Writing `app.head()` handlers or sub-app `notFound`.** HEAD is converted to GET first; `notFound` only works on the top-level app.
11. **Using v5 signatures on a v4 install (or the reverse).** Check the installed version first.

## References

Detail lives in `references/` (each section starts with its source URL):

- `references/middleware-catalog.md` - built-in and third-party middleware, import paths, auth/security notes.
- `references/helpers.md` - Factory, Cookie, Testing, Route, Streaming, Dev, and other helpers; Hono CLI.
- `references/runtimes.md` - Getting Started for Cloudflare Workers, Deno, Bun, Node, AWS Lambda, Vercel, Netlify, Fastly, Service Worker.
- `references/rpc.md` - `hc` client, status codes, `$url`/`$path`, inference helpers, performance notes.
- `references/openapi-zod.md` - `@hono/zod-openapi` (README, not hono.dev).
- `references/routers-presets.md` - routers and presets.
- `references/v5-migration.md` - v5 release-candidate breaking changes.
- `references/jsx.md` - `hono/jsx`, jsxRenderer, client components.

See also: the official `honojs/skills` repo (`npx skills add honojs/skills`) provides `hono` and `hono-jsx` agent skills. It has **not been reviewed** here; review before installing.

## Verification Checklist

- [ ] The target runtime and Hono package version (v4 vs v5 release candidate) are known from the project configuration.
- [ ] Route order does not let parameter or wildcard routes shadow specific paths; no `app.head()` handlers, no sub-app `notFound` relied on.
- [ ] Middleware order, early returns, CORS policy, and context variable types are intentional.
- [ ] All untrusted request inputs are validated before use; `json`/`form` tests send `Content-Type`.
- [ ] JSX files use `.tsx` and the configured Hono JSX runtime.
- [ ] Streaming and WebSocket paths handle aborts and the runtime adapter correctly.
- [ ] Unit tests exercise `app.request()` or `testClient()` with mocks instead of requiring a live server.
- [ ] Typed RPC routes are chained and export their `AppType` when a client or typed test helper needs them.
- [ ] The bare `hono` command is used only if `@hono/cli` is installed; no hardcoded credentials (including docs-example secrets) appear in the implementation guidance.

## See also

- `node-backend` — Node.js runtime backends and Express/Fastify comparison.
- `nextjs` — fullstack React framework with route handlers and Server Actions.
