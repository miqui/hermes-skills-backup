# OpenAPI with Zod (`@hono/zod-openapi`)

Source: https://github.com/honojs/middleware/tree/main/packages/zod-openapi (package README). **This is NOT part of hono.dev**; it is a third-party-maintained package in the honojs/middleware repo. Verify against the README before relying on specifics.

- Install `@hono/zod-openapi` (see README for peer dependencies). Import `z`, `createRoute`, `OpenAPIHono` from it; `.openapi('Name')` on a schema registers it as a referenced component.
- Define a route with `createRoute({ method, path, request: { params, query, body }, responses })`, register with `app.openapi(route, (c) => ...)` on `new OpenAPIHono()`; expose the spec with `app.doc('/doc', { openapi: '3.0.0', info: { ... } })` (`doc31` / `getOpenAPI31Document` for OpenAPI 3.1).
- Validation errors: handle per route via a hook (third arg to `app.openapi`) or globally with `new OpenAPIHono({ defaultHook: (result, c) => ... })`; a call-site hook overrides `defaultHook`.
- `app.openAPIRegistry` exposes the registry (zod-to-openapi). Per-route middleware can be set in `createRoute({ middleware: [...] })`.
- RPC mode: `hc<typeof appRoutes>` where `appRoutes = app.openapi(...)`. For large apps register routes on small `OpenAPIHono` instances and join with `.route()`, since long `.openapi()` chains grow the type.
- Batch registration: `defineOpenAPIRoute`, `openapiRoutes` (see README).
- `get()/post()/use()` return `Hono`; use `$()` or `HonoToOpenAPIHono` to get `OpenAPIHono` back.
- Swagger UI / other viewers are separate packages; check the README. Do not hardcode secrets in `security` examples.
