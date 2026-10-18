---
name: cloudflare-workers
description: Cloudflare Workers patterns for Worker runtime APIs, Durable Objects, KV, R2, D1, Queues, WebSockets, streaming responses, bindings, wrangler configuration, and deployment limits. Use when users mention Cloudflare Workers, Durable Objects, KV, R2, D1, Queues, wrangler, or edge runtime behavior.
version: '1.0'
author: epicenter
license: MIT
metadata:
  hermes:
    tags: [cloudflare, workers, durable-objects, kv, r2, d1, queues, websockets, wrangler, edge-runtime]
    related_skills: [typescript, node-backend]
---

# Cloudflare Workers

## Overview

Use this skill to implement or review applications for the Cloudflare Workers runtime. It covers Worker APIs, bindings, Durable Objects, KV, R2, D1, Queues, WebSockets, streaming responses, Wrangler configuration, runtime compatibility, and deployment limits.

## When to Use

- Building, debugging, or reviewing a Cloudflare Worker or Worker binding.
- Working with Durable Objects, KV, R2, D1, Queues, service bindings, or Hyperdrive.
- Designing Worker WebSocket, streaming, or background-work behavior.
- Changing `wrangler` configuration, compatibility dates, generated Worker types, or runtime limits.
- Integrating Hono with a Cloudflare Workers application.

## Reference Repositories

- [Cloudflare Docs](https://github.com/cloudflare/cloudflare-docs) — Workers, Durable Objects, KV, R2, D1, Queues, WebSockets, bindings, and deployment documentation.
- [Hono](https://github.com/honojs/hono) — TypeScript web framework commonly used on Workers.

## Upstream Grounding

When Worker runtime behavior, bindings, Durable Objects, WebSockets, streaming, cache APIs, service bindings, compatibility dates, limits, or Wrangler configuration affect correctness, ask DeepWiki a narrow question against `cloudflare/cloudflare-docs` before relying on memory. Use `honojs/hono` as the grounding repository when the question is about Hono on Workers.

Verify decisive details against local generated Worker types, source, or official Cloudflare documentation before changing code. Skip DeepWiki for stable Web API basics and repository-local deployment patterns already visible in the code.

## Request Lifecycle Rules

- Every async side effect must be awaited, returned, or passed to `c.executionCtx.waitUntil(...)`. Floating promises are unsafe because the isolate can stop after the response.
- Call `waitUntil` as a method on `c.executionCtx`. Do not destructure it.
- Keep `waitUntil` work bounded and best-effort. Use Queues for guaranteed or long-running work.
- For Hyperdrive plus `pg`, create a fresh `pg.Client` per request and close it after all queued work that uses the client settles. Hyperdrive is the pool.
- Node-style database drivers require `nodejs_compat` in Worker configuration.
- Skip generic response-header middleware, including CORS, for WebSocket upgrade requests. The `101` response headers are immutable.
- Put stateful or long-lived WebSockets in Durable Objects. Prefer hibernation-aware APIs when the object owns many idle sockets.
- Trust generated Worker binding types such as `Cloudflare.Env`; regenerate them when bindings or `wrangler` configuration changes.

## Common Pitfalls

1. **Floating async work after returning a response.** Await it or register it through `c.executionCtx.waitUntil(...)`; otherwise the Worker can be stopped before it completes.
2. **Using `waitUntil` for durable workloads.** `waitUntil` is bounded and best-effort. Queue work that requires delivery guarantees or may take a long time.
3. **Adding generic headers to a WebSocket upgrade response.** `101` response headers cannot be changed; bypass middleware such as CORS for upgrade requests.
4. **Treating Hyperdrive as a connection you manage globally.** It provides pooling; create and close a new `pg.Client` for each request after all client-dependent queued work settles.
5. **Hand-writing binding types.** Regenerate Worker types after changes to bindings or Wrangler configuration, then use the generated `Cloudflare.Env` types.

## Verification Checklist

- [ ] Runtime-sensitive behavior is grounded in local generated types, source, or official Cloudflare documentation.
- [ ] Every async side effect is awaited, returned, or registered with `c.executionCtx.waitUntil(...)`.
- [ ] Long-running or guaranteed work uses Queues rather than `waitUntil`.
- [ ] Worker bindings and Wrangler configuration match regenerated binding types.
- [ ] Node.js database drivers have `nodejs_compat` enabled where required.
- [ ] WebSocket upgrade paths bypass generic response-header middleware.
- [ ] Stateful or long-lived socket ownership is implemented with Durable Objects where appropriate.
