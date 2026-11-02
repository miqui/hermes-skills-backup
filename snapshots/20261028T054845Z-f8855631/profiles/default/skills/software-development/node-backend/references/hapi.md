# Hapi Reference

> Source/provenance: mechanics summarized from the official hapi.dev API documentation and the `hapijs/hapi` project, cross-checked against Hapi **21.4.10**, reviewed **2026-08-21**. Hapi's core supports a range of Node.js versions per release; version-sensitive details (supported Node versions, module compatibility) must be rechecked at **https://hapi.dev/resources/status** before relying on them, since status can change between releases.

## When to Reach for Hapi

Use Hapi when you want a configuration-centric framework with built-in route validation, a first-class plugin system, and strong conventions for large teams that prefer declarative route/server config over assembling middleware by hand. It suits APIs that lean on schema-based validation and want lifecycle extension points without composing separate middleware libraries.

## Baseline Structure

```text
src/
├── index.ts          # process entry point (init + start)
├── server.ts         # server factory (Hapi.server(...))
├── plugins/          # internal plugins (route groups, decorations)
├── routes/           # route definition modules
├── controllers/      # request handlers (thin, delegate to services)
├── services/         # business logic
├── schemas/          # Joi validation schemas
└── config/           # server/connection configuration
```

Keep the server factory separate from process bootstrap, mirroring the init/start split below, so tests can build a server without binding a port.

## Server Init/Start and Route Mechanics

Hapi separates constructing a server from starting it:

```ts
// server.ts
export const init = async () => {
  const server = Hapi.server({
    port: process.env.PORT ?? 3000,
    host: '0.0.0.0',
  });

  server.route({
    method: 'GET',
    path: '/users/{id}',
    handler: async (request, h) => {
      const user = await userService.findById(request.params.id);
      if (user == null) {
        return h.response({ message: 'Not found' }).code(404);
      }
      return user;
    },
  });

  return server;
};

// index.ts
export const start = async () => {
  const server = await init();
  await server.start();
  return server;
};
```

- `server.route()` accepts a single route or an array of routes; route options (`config`/`options`) hold validation, auth, and pre-handlers.
- Handlers return a value directly, or use the response toolkit `h` (`h.response()`, `h.redirect()`) for explicit status/header control.
- Path parameters use `{param}` syntax; optional segments use `{param?}`.

## Plugins, Decorations, and Lifecycle Extensions

Hapi plugins are the primary composition unit for grouping routes, shared state, and cross-cutting behavior:

```ts
const usersPlugin: Hapi.Plugin<undefined> = {
  name: 'users',
  register: async (server) => {
    server.route([...]);
  },
};

await server.register(usersPlugin);
```

- `server.decorate('request' | 'toolkit' | 'server', name, fn)` attaches shared helpers (e.g., a decorated `request.getUser()`), avoiding ad hoc mutation of request objects.
- `server.ext('onRequest' | 'onPreAuth' | 'onPreHandler' | 'onPreResponse', fn)` inserts lifecycle extension points for cross-cutting concerns (request IDs, response shaping) without a separate middleware abstraction.
- Keep plugins narrowly scoped (one plugin per route group/concern) so registration order stays easy to reason about.

## Joi Validation (and Optional Response Validation)

Route-level validation is declarative via Joi schemas in route options:

```ts
server.route({
  method: 'POST',
  path: '/users',
  options: {
    validate: {
      payload: Joi.object({
        email: Joi.string().email().required(),
        name: Joi.string().min(2).max(100).required(),
      }),
      params: Joi.object({ id: Joi.string().guid() }),
      query: Joi.object({ page: Joi.number().integer().min(1) }),
      failAction: async (request, h, err) => {
        throw err;
      },
    },
    // Optional: validate outgoing payloads during development/testing
    response: {
      schema: Joi.object({ id: Joi.string(), email: Joi.string() }),
      failAction: 'log',
    },
  },
  handler: createUserHandler,
});
```

- `validate.failAction` controls what happens on a validation failure; the default behavior differs by property, so set it explicitly when you need a specific error contract.
- Response validation (`options.response`) is optional and typically enabled only in development/test environments due to its runtime cost — treat it as a correctness check, not a production security control.

## Auth Plumbing (Scheme, Strategy, Defaults, Route Options)

Hapi's auth model has three layers:

1. **Scheme** — `server.auth.scheme(name, schemeFn)` defines how a credential is authenticated (e.g., inspecting a header/token).
2. **Strategy** — `server.auth.strategy(name, scheme, options)` configures a named, reusable instance of a scheme.
3. **Application** — `server.auth.default(strategyName)` sets a server-wide default, and individual routes override it with `options.auth` (a strategy name, `false` to disable, or an object for per-route tuning such as `{ strategy: '...', mode: 'try' }`).

```ts
server.auth.strategy('session', 'cookie', { /* scheme-specific options */ });
server.auth.default('session');

server.route({
  method: 'GET',
  path: '/admin',
  options: { auth: { strategy: 'session', mode: 'required' } },
  handler: adminHandler,
});
```

This reference covers only the scheme/strategy/default/route wiring mechanics. For:
- **authentication mechanism choice** (sessions, JWT, OAuth) and credential/token handling conventions across frameworks, see `references/auth.md`.
- **RBAC/ABAC modeling, permission tables, and policy enforcement architecture**, see the `application-authorization` skill.

Do not re-derive authorization policy design here — delegate to those references once the auth strategy is wired.

## Testing with `server.inject()`

Hapi's `server.inject()` runs requests through the full route/validation/lifecycle pipeline without opening a network socket, mirroring `app.inject()` in other Node frameworks:

```ts
const server = await init(); // built but not started

const res = await server.inject({
  method: 'POST',
  url: '/users',
  payload: { email: 'test@example.com', name: 'Test' },
});

expect(res.statusCode).toBe(201);
```

- Keep the init/start split so tests call `init()` only and never bind a port.
- For broader layered testing strategy (unit vs. integration boundaries, factories, database test setup), see `references/testing.md` — this section only covers the Hapi-specific inject mechanism.

## Operational / Version Compatibility Consideration

Hapi 21.4.10 is listed at Node >=16 in the hapi.dev Module Status table; package.json `engines.node` metadata may state a looser minimum, so don't treat it as the authoritative floor. Per-module and per-dependency compatibility (e.g., Joi, Hapi ecosystem plugins) can shift between patch/minor releases. Before pinning a Node version or upgrading Hapi, **recheck https://hapi.dev/resources/status** for the target core/module release rather than relying on this note.

## Common Hapi Pitfalls

1. Skipping the init/start split, making the server hard to test without binding a real port.
2. Relying on implicit `failAction` defaults instead of setting them explicitly for payload/params/query validation.
3. Enabling response validation in production paths where its runtime cost isn't justified.
4. Registering plugins in an order that breaks a decoration or lifecycle extension dependency.
5. Setting `auth` only at the server default level and assuming every route needs no override, missing routes that should be public or use a different strategy.
6. Treating scheme/strategy wiring as sufficient authorization — leaving RBAC/ABAC decisions unmodeled instead of delegating to a dedicated authorization design.

## Verification Checklist

- [ ] Server construction (`init`) is separate from `start()`
- [ ] Routes declare explicit `validate` schemas (payload/params/query) with an explicit `failAction`
- [ ] Response validation, if enabled, is scoped to non-production environments
- [ ] Plugins are narrowly scoped and registration order is intentional
- [ ] Auth strategies are named explicitly per route (or a deliberate server default is set) rather than left implicit
- [ ] RBAC/ABAC policy decisions are delegated to `application-authorization`, not embedded ad hoc in route handlers
- [ ] Tests use `server.inject()` against an un-started server instance
- [ ] Node/Hapi version compatibility was confirmed against https://hapi.dev/resources/status before upgrades
