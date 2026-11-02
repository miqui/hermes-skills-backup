# Hono v5 migration (RELEASE CANDIDATE)

Source: https://hono.dev/docs/guides/migrating-to-v5 (also in https://hono.dev/llms-full.txt). v5 is a **release candidate**: `npm install hono@next`. Verify the installed version before applying any of this; v4 projects keep v4 behavior.

## Runtime / packaging
- ESM only; CommonJS build removed. Node.js 22.12+ required; `require('hono')` still works there because 22.12 can `require()` ES modules.
- Adapters under `hono/<runtime>` are no longer bundled; install the package and import from it:

| Before | After |
| --- | --- |
| `hono/aws-lambda` | `@hono/aws-lambda` |
| `hono/bun` | `@hono/bun` |
| `hono/cloudflare-workers` | `@hono/cloudflare-workers` |
| `hono/deno` | `@hono/deno` |
| `hono/lambda-edge` | `@hono/lambda-edge` |
| `hono/netlify` | `@hono/netlify` |
| `hono/service-worker` | `@hono/service-worker` |
| `hono/vercel` | `@hono/vercel` |

- `hono/cloudflare-pages` is removed without replacement; use Workers with static assets.
- `hono/adapter` (`env()`, `getRuntimeKey()`) stays in `hono`.

## Behavior and types
- `onError()` takes middleware `(c, next)`; read `c.error` (`app.onError((c) => { console.error(c.error); return c.text('Custom Error', 500) })`). `notFound()` keeps single-handler syntax; both accept an optional path and multiple middleware. Registrations compose rather than replace; return a response to stop, or call `next()`. Paths are method-independent and relative to `basePath()`; omitted path = `*`. `route()` imports sub-app handlers incl. `notFound()`; deeper sub-apps take priority, same depth runs in registration order. Errors thrown by `onError()` middleware go to the built-in handler.
- Non-Error throws (string, plain object) now reach `onError` wrapped in an `Error`; original in `c.error.cause`, thrown string also becomes `c.error.message`. No longer propagates out of `app.fetch()`.
- `c.req.query()` / `c.req.queries()` without a key: `Record<string, string | undefined>` / `Record<string, string[] | undefined>`.
- `c.req.json()` returns `Promise<unknown>` (was `any`); use `c.req.json<T>()` or a validator + `c.req.valid()`.
- `c.json(undefined)` (also function/symbol) throws `TypeError`, like `Response.json()`.
- Wildcards identical in every router: trailing `*` in a segment is a wildcard and may match nothing; `*` mid-segment (`/x*y`) is not a wildcard; a segment that is only `*` matches one non-empty segment. In RegExpRouter, `/x*/y` and `/x/*` cannot be registered together (`UnsupportedPathError`; SmartRouter falls back to TrieRouter).
- `getColorEnabledAsync()` (`hono/utils/color`) removed; use `getColorEnabled(c.env)`. `logger()` handles it itself.

## Removed deprecated features
- `app.mount()` -> `app.all('/x/*', mount(handler))` with `import { mount } from 'hono/mount'`.
- `app.fire()` -> `fire(app)` from `@hono/service-worker`.
- `c.req.matchedRoutes` / `c.req.routePath` -> `matchedRoutes(c)` / `routePath(c)` from `hono/route`.
- `toSSG()` hook options `beforeRequestHook`, `afterResponseHook`, `afterGenerateHook` -> pass via `plugins: [{ beforeRequestHook }, defaultPlugin()]` (`defaultPlugin()` is applied only when `plugins` is omitted).
- Bearer Auth: `noAuthenticationHeaderMessage`/`invalidAuthenticationHeaderMessage`/`invalidTokenMessage` -> `noAuthenticationHeader.message`/`invalidAuthenticationHeader.message`/`invalidToken.message`.
- Serve Static: `pathResolve` option removed. SSG: `SSG_DISABLED_RESPONSE` -> `X_HONO_DISABLE_SSG_HEADER_KEY`.
- `timingSafeEqual()` (`hono/utils/buffer`) accepts strings only; `hashFunction` for Basic/Bearer Auth typed `(input: string) => string | null | Promise<string | null>`.
- `getQueryStrings()` (`hono/utils/url`) removed (use `URL`); `UnOfficalStatusCode` -> `UnofficialStatusCode`.
