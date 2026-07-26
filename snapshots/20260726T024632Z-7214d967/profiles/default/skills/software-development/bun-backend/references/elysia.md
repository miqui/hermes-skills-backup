# Elysia Reference

## Overview

Elysia is the default framework reference for Bun-native backend APIs in this corpus. It is TypeScript-first and emphasizes end-to-end type inference, schema-driven validation, plugin composition, OpenAPI generation, and testable app handlers.

Use Elysia when the task involves:
- building a Bun API or service from scratch
- designing typed REST endpoints
- composing plugins and shared context cleanly
- using schema-driven validation and typed request/response contracts
- generating OpenAPI docs from route schemas
- building realtime endpoints with WebSocket support
- testing Bun HTTP handlers without binding real ports

Prefer BurgerAPI instead when file-based routing and framework-provided scaffolding are central to the project design.

## Canonical Docs

- Main site: https://elysiajs.com/
- Quick Start: https://elysiajs.com/quick-start.html
- Route: https://elysiajs.com/essential/route.html
- Plugin: https://elysiajs.com/essential/plugin.html
- Validation: https://elysiajs.com/essential/validation.html
- Best Practice: https://elysiajs.com/essential/best-practice.html
- Error Handling: https://elysiajs.com/patterns/error-handling.html
- OpenAPI: https://elysiajs.com/patterns/openapi.html
- TypeBox / Elysia.t: https://elysiajs.com/patterns/typebox.html
- TypeScript: https://elysiajs.com/patterns/typescript.html
- Unit Test: https://elysiajs.com/patterns/unit-test.html
- WebSocket: https://elysiajs.com/patterns/websocket.html
- Deploy to Production: https://elysiajs.com/patterns/deploy.html

## Mental Model

Think of Elysia as a Bun-native framework where:

- routes are declared fluently in code
- validation and TypeScript types are derived from schemas
- plugins compose shared behavior and typed context
- the app can be exported as a handler for tests and imported by a small bootstrap entrypoint

Minimal shape:

```ts
import { Elysia, t } from 'elysia'

export const app = new Elysia()
  .get('/health', () => ({ ok: true }))
  .post(
    '/users',
    ({ body, set }) => {
      set.status = 201
      return { email: body.email, name: body.name }
    },
    {
      body: t.Object({
        email: t.String({ format: 'email' }),
        name: t.String({ minLength: 1 })
      }),
      response: {
        201: t.Object({
          email: t.String(),
          name: t.String()
        })
      },
      detail: {
        summary: 'Create a user'
      }
    }
  )
```

Bootstrap separately:

```ts
import { app } from './app'

app.listen(Number(Bun.env.PORT ?? 3000))
console.log(`Listening on ${app.server?.url}`)
```

## Recommended Project Structure

For medium-sized Elysia backends, prefer explicit modules over framework magic:

```text
src/
  index.ts              # bootstrap / listen only
  app.ts                # root Elysia app without listen side effects
  plugins/              # db, auth, config, logger, docs
  routes/               # route groups by domain
  schemas/              # shared request/response schemas
  services/             # business logic
  lib/                  # utilities / adapters
test/
  *.test.ts
```

Boundaries:

- routes own transport shape, schemas, status codes, and framework context
- services own business logic and side effects
- plugins provide shared dependencies and request context
- schemas are reused when they improve consistency, not extracted prematurely

## Key Patterns

### 1. Keep routes thin

Handlers should orchestrate and translate HTTP concerns, not contain the whole workflow.

```ts
app.post('/orders', async ({ body, set, orderService }) => {
  const order = await orderService.create(body)
  set.status = 201
  return { data: order }
})
```

### 2. Use plugins for shared context

Put database clients, auth helpers, config, logger, and docs setup into plugins or explicit modules.

```ts
import { Elysia } from 'elysia'

export const dbPlugin = new Elysia({ name: 'db' })
  .decorate('db', createDbClient())
```

Keep plugin names stable when they influence type inference or composition.

### 3. Treat schemas as contracts

Use `Elysia.t` / TypeBox-style schemas for request validation, response validation where useful, and OpenAPI generation.

```ts
import { Elysia, t } from 'elysia'

app.get('/users/:id', ({ params }) => params, {
  params: t.Object({
    id: t.String()
  })
})
```

### 4. Add OpenAPI deliberately

For consumer-facing APIs, add the current Elysia OpenAPI plugin and review generated output as a contract:

```ts
import { openapi } from '@elysiajs/openapi'
import { Elysia } from 'elysia'

export const app = new Elysia()
  .use(openapi())
```

Some older examples use `@elysiajs/swagger`. Check the project's installed plugin and current docs before changing package names.

### 5. Centralize error handling

Use `onError` for consistent validation, not-found, authorization, and unexpected error responses. Keep diagnostic details in logs, not client responses.

```ts
new Elysia()
  .onError(({ code, error, set }) => {
    if (code === 'VALIDATION') {
      set.status = 400
      return { code: 'VALIDATION_ERROR', message: 'Invalid request' }
    }

    if (code === 'NOT_FOUND') {
      set.status = 404
      return { code: 'NOT_FOUND', message: 'Not found' }
    }

    set.status = 500
    return { code: 'INTERNAL_ERROR', message: 'Internal server error' }
  })
```

### 6. Test through app handlers

Use `bun:test` and `app.handle()` or `app.fetch()` style tests so routes, schemas, errors, and plugins are exercised without binding a real port.

```ts
import { describe, expect, it } from 'bun:test'
import { app } from '../src/app'

describe('health', () => {
  it('returns ok', async () => {
    const response = await app.handle(new Request('http://localhost/health'))
    expect(response.status).toBe(200)
    await expect(response.json()).resolves.toEqual({ ok: true })
  })
})
```

### 7. Use WebSocket only where realtime matters

Elysia makes WebSocket support approachable, but realtime protocols still need auth, event schemas, lifecycle handling, heartbeats, and scaling decisions. Do not introduce WebSockets when HTTP polling or server-sent events would be simpler.

## Integration Notes

### Auth

Keep auth setup isolated in a plugin or module boundary. Authenticate at the boundary, attach typed context, and keep object-level authorization in services or policy helpers.

### Database

Drizzle is a common fit for type-safe SQL. Prisma or other database clients can also work when the repo already standardizes on them. Keep query logic out of route handlers.

### OpenAPI

Generated docs are not automatically high-quality API design. For external APIs, pair with `openapi-api-designer` and review operation names, descriptions, examples, errors, and auth semantics.

## When to Choose Elysia Over BurgerAPI

Choose Elysia when you want:

- explicit code-first route composition
- plugin-based app architecture
- strong TypeScript inference from schemas
- flexible APIs, auth, docs, and realtime support
- easy handler-level tests with `bun:test`

Choose BurgerAPI when you want file-based routing to drive the application structure.

## Common Pitfalls

1. Putting too much business logic directly in route handlers.
2. Treating inferred types as a substitute for domain boundaries.
3. Extracting many tiny plugins before the codebase needs them.
4. Skipping schemas or OpenAPI for externally consumed endpoints.
5. Assuming generated OpenAPI output is automatically consumer-friendly.
6. Overusing realtime/WebSocket patterns where regular HTTP is simpler.
7. Binding a real port in tests instead of exporting an app handler.

## Verification Checklist

- [ ] Routes validate request shape with schemas where it matters
- [ ] Shared infrastructure is provided through plugins or explicit modules
- [ ] Business logic stays outside handlers
- [ ] Error responses are stable and do not leak internals
- [ ] OpenAPI/docs are enabled and reviewed for consumer-facing APIs
- [ ] Tests run through `bun test` and exercise app handlers without unnecessary ports
- [ ] Framework choice still matches the project's routing and architecture needs
