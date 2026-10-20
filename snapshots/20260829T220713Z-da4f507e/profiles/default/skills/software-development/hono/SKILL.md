---
name: hono
description: Use when building, testing, reviewing, or debugging Hono applications, including Hono routing, middleware, request validation, JSX, streaming, WebSockets, typed RPC clients, and runtime adapters.
metadata:
  version: '1.1'
tags: [hono, typescript, web-framework, routing, middleware, cloudflare-workers, edge]
---

# Hono

## Overview

Hono is a TypeScript web framework built on Web Standards that runs on Cloudflare Workers, Deno, Bun, Node.js, and other runtimes. Use this skill for application behavior and framework patterns; pair it with the runtime-specific skill when platform bindings, deployment configuration, or runtime limits matter.

## When to Use

- Code imports from `hono` or `hono/*`.
- Building or reviewing Hono routes, middleware, request handling, validation, rendering, streaming, WebSockets, or RPC clients.
- Working with Hono on Cloudflare Workers, Node.js, Bun, or Deno.
- Testing an app through `app.request()` or `testClient()` without first starting an HTTP server.

Do not use this skill as the source of truth for a runtime's deployment configuration, bindings, or limits. For Cloudflare Workers-specific lifecycle and binding behavior, also load `cloudflare-workers`.

## Documentation and Version Grounding

- Start with the official Hono documentation for framework APIs. For behavior that depends on a package version, verify the project's lockfile plus installed types or source before changing code.
- Treat local project conventions and existing app composition as authoritative unless they conflict with Hono's documented API.
- Check the runtime adapter's documentation before assuming an API works identically on Workers, Node.js, Bun, or Deno.
- Do not use unscoped `npx hono ...` commands: the `hono` package does not provide that executable. Prefer the portable APIs in this skill, especially `app.request()` and `testClient()`.

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
app.onError((err, c) => {
  console.error(err)
  return c.json({ message: 'Internal Server Error' }, 500)
})
```

- Register routes and middleware in deliberate order. Specific routes must precede broad parameter or wildcard routes that could match them.
- Use `app.route('/api', api)` to mount a feature sub-app, or `new Hono().basePath('/api')` for a scoped app.
- Keep handlers close to their route definitions when path-parameter and response inference matters.
- Return `c.json()`, `c.text()`, `c.html()`, `c.redirect()`, `c.body()`, or a `Response`; do not leave a handler without a response.

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

- Use `c.req.param()`, `query()`, `queries()`, and `header()` for URL and header inputs.
- Parse each body once with the appropriate method: `json()`, `text()`, `formData()`, `parseBody()`, `arrayBuffer()`, or `blob()`.
- Pass request-scoped values through `c.set('key', value)` and retrieve them with `c.var.key` or `c.get('key')`; do not use module-global mutable request state.
- On Workers, access bindings through `c.env` and request-lifetime work through `c.executionCtx`. Follow runtime-specific lifecycle guidance for `waitUntil()` and WebSockets.

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
- Register CORS before authentication when credentialed cross-origin browser requests require preflight handling; keep the CORS policy narrowly scoped.
- Use built-in middleware such as `cors`, `logger`, `secureHeaders`, `csrf`, `bearerAuth`, or `jwt` only where their behavior matches the route and deployment model.
- Use `createFactory<Env>()` when an app, middleware, and separately defined handlers need the same `Env` type.
- Keep WebSocket-upgrade detection explicit. Do not apply generic response-header middleware to a runtime path whose upgrade response headers are immutable.

## Validation

Validate each untrusted request part before using it. Hono supports multiple validators on the same route for parameters, query strings, headers, forms, and JSON bodies.

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

- Use `c.req.valid('json')`, `valid('query')`, `valid('param')`, or `valid('form')` only after the matching validator has run.
- `@hono/standard-validator` is appropriate when the project uses a Standard Schema-compatible library such as Valibot; do not introduce a second validation ecosystem without a project-level reason.
- Return a safe validation error and avoid parsing the same body separately in downstream middleware or handlers.

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

Use a renderer or `jsxRenderer` for shared layouts. Keep async data access inside async components or handlers, and render escaped values through JSX rather than interpolating untrusted strings as raw HTML.

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
- WebSocket upgrades require the runtime's matching adapter. Keep connection ownership and lifecycle rules runtime-specific.

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
- Test middleware rejection, validation failures, not-found behavior, and error mapping—not only successful handlers.

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
- Keep server and client package versions compatible; type inference problems are often caused by split or duplicate Hono versions.

## Runtime Adapters

```ts
// Cloudflare Workers, Deno, or Bun
export default app

// Node.js
import { serve } from '@hono/node-server'
serve(app)
```

- Install and use the adapter that matches the actual runtime; do not assume the default export starts a Node HTTP server.
- Keep framework logic portable, but isolate runtime bindings, upgrade handling, and deployment configuration at the adapter boundary.

## Common Pitfalls

1. **Registering a broad route before a specific route.** Hono uses registration order; move the specific route first.
2. **Calling `await c.req.json()` more than once.** Parse once, validate once, and pass the typed result forward.
3. **Using `c.req.valid()` without matching validator middleware.** Add and order the validator before the handler.
4. **Losing RPC or `testClient` inference.** Chain the route declarations and export the type of the chain.
5. **Putting JSX in a `.ts` file.** Rename it to `.tsx` and set `jsxImportSource` to `hono/jsx`.
6. **Testing only through a live server.** Start with `app.request()` plus mock bindings for fast, deterministic tests.
7. **Hardcoding credentials in authentication middleware.** Obtain them from the runtime's approved configuration or secret store; never place real credentials in source, tests, or command arguments.
8. **Treating Workers and Node as interchangeable.** Verify adapter, bindings, WebSocket, and lifecycle behavior for the deployed runtime.

## Verification Checklist

- [ ] The target runtime and Hono package version are known from the project configuration.
- [ ] Route order does not let parameter or wildcard routes shadow specific paths.
- [ ] Middleware order, early returns, CORS policy, and context variable types are intentional.
- [ ] All untrusted request inputs are validated before use.
- [ ] JSX files use `.tsx` and the configured Hono JSX runtime.
- [ ] Streaming and WebSocket paths handle aborts and the runtime adapter correctly.
- [ ] Unit tests exercise `app.request()` or `testClient()` with mocks instead of requiring a live server.
- [ ] Typed RPC routes are chained and export their `AppType` when a client or typed test helper needs them.
- [ ] No unscoped `npx hono` commands, hardcoded credentials, or unverified third-party CLI fallback appears in the implementation guidance.
