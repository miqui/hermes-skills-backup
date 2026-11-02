# Helpers and Hono CLI

Sources: https://hono.dev/docs/helpers/<name>, https://hono.dev/docs/guides/best-practices, https://hono.dev/docs/api/exception, https://hono.dev/docs/api/context (all in https://hono.dev/llms-full.txt). Details not listed: verify against docs.

## Hono CLI (`@hono/cli`)
Source: https://hono.dev/llms-full.txt ("Hono CLI" section; locate the page slug on hono.dev). The `hono` binary exists only when `npm install -D @hono/cli` (or `-g`). It loads the app directly; no server. Output is JSON (`{ "ok": true, "data": ... }` or `{ "ok": false, "error": {code,message,suggestions,docs} }`, exit 1).
- `hono routes [file] [--verbose|--plain]`, `hono request [path] [file] [-X -d -H --trace --runtime node|bun|deno|workerd|vite --no-bindings]`, `hono batch <source> [file]` (JSONL with `method,path,body,headers,expect,save`; `{{id}}` substitution), `hono snapshot [file] [--status-only]`, `hono diff [--base <ref>]`, `hono benchmark`, `hono ssg`, `hono init`.
- App file default: `src/index.ts|tsx|js|jsx`. With a wrangler config `c.env` gets real local bindings (unless `--no-bindings`). `snapshot`/`diff`/`batch` send real requests, so middleware and side effects run.
- Without it: `app.request()` / `testClient()`.

## Factory (`hono/factory`)
- `createFactory<Env>({ defaultAppOptions, initApp })`; `factory.createApp()`, `factory.createMiddleware()`, `factory.createHandlers(...)` (`app.get('/api', ...handlers)`); `createMiddleware<Env>(async (c, next) => {...})` standalone. `createFactory` avoids declaring `Env` twice. Docs best-practices: do not make Rails-style controllers with a bare `Context` (path params are not inferred); write handlers inline or use `createHandlers()`, and split apps with `app.route()`.

## Exceptions
- `HTTPException(status, { message | res, cause })`; `err.getResponse()` in `app.onError`; it is not Context-aware, so headers set on `c` must be re-applied to a new `Response`.

## Other helpers
- Accepts: `hono/accepts` `accepts`. Adapter: `hono/adapter` `env(c)`, `getRuntimeKey()`. ConnInfo: runtime-specific `getConnInfo`. Cookie: `hono/cookie` `getCookie/setCookie/deleteCookie`, signed cookies are async (HMAC SHA-256), `prefix: 'secure'|'host'` for `__Secure-`/`__Host-`. css: `hono/css` (`css`, `cx`, `keyframes`, `Style`, `createCssContext`). html: `hono/html` (`html`, `raw`). Proxy: `hono/proxy` `proxy(url, init)` (fetch wrapper; do not forward all request headers/credentials unless needed). Route: `hono/route` `routePath`, `matchedRoutes`, `baseRoutePath`, `basePath`. SSG: `hono/ssg` `toSSG`, `defaultPlugin`, `redirectPlugin`. Streaming: `hono/streaming` `stream`, `streamText`, `streamSSE` (`onAbort`; on Workers under Wrangler, `Content-Encoding: Identity` may be needed for `streamText`). Dev: `hono/dev` `showRoutes`, `getRouterName`. Testing: `hono/testing` `testClient(app)` (routes must be chained on the Hono instance for inference).
- WebSocket helper: `upgradeWebSocket` from the runtime package (`@hono/cloudflare-workers`, `@hono/deno`, `@hono/bun` + `websocket`, `@hono/node-server`). Header-modifying middleware (e.g. CORS) on a WebSocket route can fail with "immutable headers" because `upgradeWebSocket()` changes headers internally.

## Context facts
- `c.req.header()` no-arg returns lowercase keys. `c.error` set after `next()` if a handler threw. `c.res` can be replaced after `next()`. Chained `.use()` accumulates `Variables` types. HEAD becomes GET so `app.head()` never runs. Strict routing by default.
