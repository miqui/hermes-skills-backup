---
name: hapi
description: "Build/test Hapi Node.js APIs: routes, plugins, Joi, auth."
metadata:
  version: '1.0'
tags: [hapi, nodejs, joi, plugins, authentication, validation, testing, api]
related_skills: [node-backend, openapi-api-designer, api-governance]
---

# Hapi

## Overview

Hapi (`@hapi/hapi`) is a config-driven Node.js server framework built by an OAuth co-author, favoring explicit route/plugin configuration over middleware chains. Use this skill for Hapi-specific mechanics — server/route/plugin primitives, Joi-based validation, the scheme/strategy auth model, and the official `lab`/`code` testing stack. For vendor-neutral REST contract design, pair with `openapi-api-designer` / `api-governance`; for general Node backend architecture patterns not specific to Hapi, see `node-backend`.

## When to Use

- Code imports `@hapi/hapi`, `@hapi/joi`/`joi`, `@hapi/boom`, `@hapi/lab`, `@hapi/code`, or hapi ecosystem plugins (`@hapi/basic`, `@hapi/cookie`, `@hapi/jwt`, `@hapi/inert`, `@hapi/vision`, `@hapi/h2o2`).
- Building or reviewing Hapi servers, routes, plugins, request lifecycle extensions, or the response toolkit (`h`).
- Adding/reviewing input or output validation, authentication schemes/strategies, or caching via catbox.
- Writing or reviewing tests that use `server.inject()`.

Do not use this skill as the source of truth for generic REST API contract design (OpenAPI shape, resource modeling) — pair with `openapi-api-designer`/`api-governance` for that.

## Documentation and Version Grounding

- Official docs: https://hapi.dev/api/ (versioned API reference) and https://hapi.dev/tutorials/ (Getting Started, Validation, Testing, Authentication, Plugins, Caching, Routing, Server Methods, Views).
- Current API reference default is **hapi v21.4.10**; requires **Node.js >= 16** (v12 support dropped). Some newer ecosystem modules require Node >= 22 — always check the live compatibility table at https://hapi.dev/resources/status before assuming a floor.
- Each hapi-org module (joi, boom, catbox, inert, vision, hoek, wreck, lab, code, jwt, cookie, basic, ...) is versioned and released independently; verify the specific module version + Node floor on the Module Status page rather than assuming parity with core hapi.
- Full research notes and citations: `references/hapi-official-docs.md`.

## Server, Routes, and Plugins

```js
'use strict';
const Hapi = require('@hapi/hapi');

const init = async () => {
    const server = Hapi.server({ port: 3000, host: 'localhost' });

    server.route({
        method: 'GET',
        path: '/hello/{name}',
        handler: (request, h) => `Hello ${request.params.name}!`,
    });

    await server.start();
};
```

- Plugins are `{ name, version, register: async (server, options) => {} }`, loaded via `server.register(plugin, [options])`; use `prefix`/`vhost` registration options to namespace plugin routes, and `multiple`/`once` to control re-registration behavior.
- Prefer decomposing an API into plugins per bounded-context/feature rather than one flat route file — this is Hapi's primary structuring mechanism (no middleware chain equivalent).
- Server-side caching goes through **catbox** (memory by default; Redis/Memcached/MongoDB/Riak providers available) — only used when methods/plugins explicitly opt in.

## Validation (Joi)

```js
server.route({
    method: 'POST',
    path: '/post',
    handler: (request, h) => 'Blog post added',
    options: {
        validate: {
            payload: Joi.object({
                post: Joi.string().min(1).max(140),
                date: Joi.date().required(),
            }),
        },
    },
});
```

- `route.options.validate.{headers,params,query,payload,state}` accept a Joi schema or an `async function(value, options)`; a key set to `true` skips validation for that input.
- If you validate one query/payload key, you must validate **all** accepted keys for that input — unlisted keys are rejected by default (400 `Bad Request`).
- Output/response validation is a separate concern: `route.options.response.{schema, sample, status, options, failAction}` validates responses before they leave the server.
- Compatible with hapi v17+ and joi v16+ per official tutorial.

## Authentication (Schemes and Strategies)

- **Scheme** = an auth method implementation (`@hapi/basic`, `@hapi/cookie`, `@hapi/jwt`, or hand-written) exposing `authenticate(request, h)` (required) plus optional `payload`/`response` hooks.
- **Strategy** = a named, configured instance of a scheme, registered via `server.auth.strategy(name, schemeName, options)`.
- On success, a scheme must call `h.authenticated({ credentials, artifacts })`; on failure, throw or return `h.unauthenticated(error, [data])` — use `@hapi/boom` for the error.
- Set a global default with `server.auth.default(strategyNameOrObject)` — this applies even to routes registered before the call.
- Per-route override: `route.options.auth` = `false` (disable) | strategy name string | `{ mode: 'required'|'optional'|'try', strategies, payload }`.

## Testing (lab + code, or any runner)

Hapi is designed to test routes without opening a real socket, via `server.inject()` (built on Shot):

```js
// lib/server.js — export init() (no listen) separately from start() (listens)
exports.init = async () => {
    await server.initialize();
    return server;
};
exports.start = async () => {
    await server.start();
    return server;
};
```

```js
const Lab = require('@hapi/lab');
const { expect } = require('@hapi/code');
const { afterEach, beforeEach, describe, it } = (exports.lab = Lab.script());
const { init } = require('../lib/server');

describe('GET /', () => {
    let server;
    beforeEach(async () => { server = await init(); });
    afterEach(async () => { await server.stop(); });

    it('responds with 200', async () => {
        const res = await server.inject({ method: 'get', url: '/' });
        expect(res.statusCode).to.equal(200);
    });
});
```

- Official stack is `@hapi/lab` (async/await-only test runner) + `@hapi/code` (chai-based assertions), but `server.inject()` works equally well with Mocha, Jest, Tap, or Ava — the pattern (not the runner) is what matters.
- Always split server construction into `init()` (initialize only, for tests) vs `start()` (actually listens) so tests never bind a real port.

## Quick Reference

```text
Server      → Hapi.server({ port, host, ... })
Routes      → server.route({ method, path, handler, options })
Plugins     → { name, version, register: async (server, options) => {} }
Validation  → route.options.validate.{headers,params,query,payload} (Joi)
Response    → route.options.response.{schema,sample,status,failAction}
Auth        → server.auth.scheme/strategy/default; route.options.auth
Caching     → catbox providers (memory default; Redis/Memcached/Mongo/Riak)
Testing     → server.inject() + @hapi/lab + @hapi/code (or Jest/Mocha/Tap/Ava)
Errors      → @hapi/boom for HTTP-friendly thrown errors
Node floor  → >= 16 for core hapi v21.x; verify per-module at hapi.dev/resources/status
```

## Common Pitfalls

1. Validating one query/payload key but forgetting others — unlisted keys get rejected, not ignored.
2. Calling `start()` (which binds a real port) inside tests instead of `init()` — always split the two exports.
3. Assuming a single Node.js version floor across the whole ecosystem — each hapi-org module has its own; check the Module Status page rather than assuming parity with core `@hapi/hapi`.
4. Treating hapi plugins like Express middleware (implicit chain) — hapi has no middleware equivalent; use plugins, route `pre` handlers, and server extension points instead.
5. Forgetting `server.auth.default()` retroactively applies to routes registered before the call — order still matters when reasoning about which routes require auth.
6. Not using `@hapi/boom` for thrown auth/scheme errors — plain `Error` throws lose the HTTP-shaped response.

## Verification Checklist

- [ ] Routes group into plugins by feature/bounded-context, not one flat file.
- [ ] All accepted query/payload/header keys are listed in the Joi validate schema (or `true`/omitted to skip entirely).
- [ ] Response/output validation is set where the API makes response-shape guarantees.
- [ ] Auth strategies are registered before being referenced by name, and route-level `options.auth` is set intentionally (not left to an unexamined default).
- [ ] Tests use `server.inject()` against `init()`, never a live-started server bound to a port.
- [ ] Errors surfaced to clients are `@hapi/boom` errors, not raw `Error` objects.
- [ ] Node.js version and per-module compatibility were checked against https://hapi.dev/resources/status rather than assumed.
