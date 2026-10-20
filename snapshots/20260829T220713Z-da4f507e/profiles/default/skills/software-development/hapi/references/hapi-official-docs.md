# Hapi Official Documentation — Research Notes

Compiled from hapi.dev and github.com/hapijs/hapi (official sources only). Use this
as a starting map; re-verify against the live pages for anything version-sensitive.

## Version / compatibility

- Current documented API reference version: **hapi v21.4.10** — https://hapi.dev/api/
- GitHub `hapijs/hapi` release tags list 20.3.0 as "Latest" release artifact, but
  21.x is the active line reflected in the versioned docs and package.json on
  `master`. Node v12 support was dropped (see repo history, commit "Drop node v12
  support (#4346)").
- **Node.js floor: >= 16** for `@hapi/hapi` core and most first-party modules
  (joi, boom, catbox*, hoek, wreck, inert, vision, lab, code, jwt, cookie, basic,
  crumb, glue, h2o2, nes, podium, statehood, subtext, topo, vise, ...).
- A handful of newer/smaller utility modules require **Node >= 22** (e.g. `bell`
  adjacent utilities, `oxc-plugin`, `sse` at time of research) — always check the
  live table rather than assuming a single floor across the ecosystem.
- Authoritative, continuously updated compatibility table (module, version, license,
  Node floor) for the whole hapi-org ecosystem:
  **https://hapi.dev/resources/status**
- GitHub repo: https://github.com/hapijs/hapi (14.8k stars, 379 tags, BSD license,
  Technical Steering Committee model — @devinivy, @lloydbenson, @nlf, @geek,
  @marsup, @jonathansamines at time of research).

## Core primitives — https://hapi.dev/api/

- `Hapi.server([options])` — main server object/container. Options include
  `address`, `app` (app-specific config bag, distinct from `server.app` runtime
  state), `autoListen`, `cache` (catbox provider config, default in-memory),
  `compression` (`minBytes` threshold), `debug` (console logging tags for dev).
- Route object: `{ method, path, handler, options }`. `options.validate`,
  `options.response`, `options.auth`, `options.cache` all live here.
- Request lifecycle: hapi documents explicit extension points (onRequest,
  onPreAuth, onPostAuth, onPreHandler, onPostHandler, onPreResponse, etc.) —
  this replaces the middleware-chain model used by Express/Koa.
- Plugins: `{ name, version, register: async (server, options) => {} }` or with
  `pkg: require('./package.json')` instead of explicit name/version.
  `server.register(plugin_or_array, [options])`; registration options support
  `routes.prefix` and `routes.vhost` to namespace a plugin's routes, plus
  `multiple`/`once` plugin-object flags for re-registration semantics.
- Caching: hapi ships a default in-memory cache via **catbox**; production
  deployments typically swap in `@hapi/catbox-redis`, `catbox-memcached`,
  `catbox-mongodb`, etc. Caching only activates when server methods or plugins
  explicitly read/write through it.

## Validation — https://hapi.dev/tutorials/en_US/validation

- Compatible with hapi v17+ and joi v16+ (per tutorial header note).
- `route.options.validate` default value:
  `{ headers: true, params: true, query: true, payload: true, state: true, failAction: 'error' }`.
  A value of `true` disables validation for that input; a Joi schema or an
  `async function(value, options)` enables it.
- Validating one key of `query`/`payload` means you must validate **every**
  accepted key for that input — anything not declared is rejected (HTTP 400,
  `"Invalid request {params|query|payload} input"`).
- Output/response validation is a separate, opt-in mechanism under
  `route.options.response`: `schema`, `sample` (percentage of responses to
  validate, for perf), `status` (per-status-code schemas), `options`
  (Joi options), `failAction`.
- Headers can be validated too (`validate.headers`), commonly paired with
  `options: { allowUnknown: true }` so unlisted headers aren't rejected.

## Testing — https://hapi.dev/tutorials/en_US/testing

- Compatible with hapi v17+.
- Hapi is designed to test routes **without starting a real server** — via
  `server.inject()`, built on the **Shot** library, which injects a simulated
  HTTP request directly into the route handler (no socket/TCP overhead).
- Official recommended stack: `@hapi/lab` (test runner, async/await only,
  `npm install --save-dev @hapi/lab`) + `@hapi/code` (chai-based assertion
  library, `npm install --save-dev @hapi/code`). Explicitly noted as
  interchangeable with Mocha, Jest, Tap, Ava — the pattern is what's official,
  not the specific runner.
- Canonical pattern: export `init()` (calls `server.initialize()` — starts
  caches/finalizes plugin registration, does NOT bind a port) separately from
  `start()` (calls `server.start()` — actually listens). Tests call `init()` in
  `beforeEach`/setup and `server.stop()` in `afterEach`/teardown; the real
  entrypoint file calls `start()`.
- `lab` defaults to running all `*.js` under a local `test/` directory; typical
  `package.json` script: `"test": "lab -v **/*.test.js"`.

## Authentication — https://hapi.dev/tutorials/en_US/auth

- Compatible with hapi v17+.
- Two-layer model: **scheme** (an auth method implementation, signature
  `function(server, options)` returning an object with required `authenticate`
  and optional `payload`/`response` methods) and **strategy** (a named,
  pre-configured instance of a scheme, created with
  `server.auth.strategy(name, schemeName, [options])`).
- `authenticate(request, h)`: on success must call/return
  `h.authenticated({ credentials, artifacts })`; on failure, throw or return
  `h.unauthenticated(error, [data])`. `credentials`/`artifacts` become available
  later via `request.auth`. Official recommendation: use **@hapi/boom** for
  errors thrown here.
- `payload(request, h)`: optional scheme hook, signal success with `h.continue`,
  signal failure by throwing (boom recommended).
- `response(request, h)`: optional scheme hook to decorate `request.response`
  with headers before sending; must return `h.continue` when done, or throw
  (boom recommended) on error.
- `server.auth.default(nameOrObject)` sets a server-wide default strategy/config
  — explicitly noted to apply retroactively to routes registered *before* the
  call.
- Per-route override via `route.options.auth`: `false` disables auth for that
  route; a string names a specific strategy; an object supports `mode`
  (`'required' | 'optional' | 'try'`), `strategies` (array for multi-strategy
  routes), and `payload`.
- Common official/community scheme plugins referenced: `@hapi/basic`,
  `@hapi/cookie` (both explicitly named as example schemes in the tutorial);
  `@hapi/jwt` also tracked on the Module Status page.

## Plugins — https://hapi.dev/tutorials/en_US/plugins

- Compatible with hapi v17+.
- Minimal plugin shape and the `pkg`-based external-module variant are both
  officially sanctioned; a plugin module can be the top-level export
  (`module.exports = { register, name, version }`) or `exports.plugin = {...}`
  if the module also exports other things.
- `multiple: true` on the plugin object allows safe repeated registration in
  the same server; `once: true` makes hapi silently ignore subsequent
  registrations of the same plugin instead of throwing.
- `server.register(plugins, [options])` accepts a single plugin or an array of
  `{ plugin, options }` objects. The second `server.register()` argument (as
  opposed to the plugin's own `options`) is consumed by hapi itself, not passed
  to the plugin — it supports `routes.prefix` and `routes.vhost` to namespace
  all routes the plugin creates.

## Citations (all consulted this session)

- https://hapi.dev/
- https://hapi.dev/api/ (v21.4.10)
- https://hapi.dev/tutorials/en_US/validation
- https://hapi.dev/tutorials/en_US/testing
- https://hapi.dev/tutorials/en_US/auth
- https://hapi.dev/tutorials/en_US/plugins
- https://hapi.dev/resources/status
- https://github.com/hapijs/hapi
