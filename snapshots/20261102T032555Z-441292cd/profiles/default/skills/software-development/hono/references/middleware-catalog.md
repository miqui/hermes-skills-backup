# Middleware catalog

Sources: https://hono.dev/docs/middleware/builtin/<name> and https://hono.dev/docs/middleware/third-party (in https://hono.dev/llms-full.txt). Option names beyond those listed: verify against docs. Docs examples sometimes show literal secrets; use `c.env`/`process.env` instead.

## Built-in (import from `hono/<name>`)
| Middleware | Import | Notes |
| --- | --- | --- |
| Basic Auth | `hono/basic-auth` `basicAuth` | needs username/password from env, not literals |
| Bearer Auth | `hono/bearer-auth` `bearerAuth` | v5: message options renamed (`noAuthenticationHeader.message` ...) |
| Body Limit | `hono/body-limit` `bodyLimit` | `maxSize` default 100KB; uses Content-Length, else streams; `onError`. Bun needs `maxRequestBodySize` for larger |
| Cache | `hono/cache` `cache` | verify against docs (platform Cache API) |
| Combine | `hono/combine` `some`, `every`, `except` | compose middleware conditionally |
| Compress | `hono/compress` | verify against docs |
| Context Storage | `hono/context-storage` | verify against docs |
| CORS | `hono/cors` `cors` | "CORS should be called before the route"; default allowMethods `['GET','HEAD','PUT','POST','DELETE','PATCH','QUERY']`; allowMethods may be a callback |
| CSRF | `hono/csrf` `csrf` | checks `Origin` and `Sec-Fetch-Site` (allowed if either passes); only unsafe methods with form content types (`application/x-www-form-urlencoded`, `multipart/form-data`, `text/plain`); options for allowed `origin` and `secFetchSite` values |
| ETag | `hono/etag` `etag`, `RETAINED_304_HEADERS` | |
| IP Restriction | `hono/ip-restriction` `ipRestriction` | needs runtime conninfo (`getConnInfo`) |
| JSX Renderer | `hono/jsx-renderer` `jsxRenderer`, `useRequestContext` | see `jsx.md` |
| JWK Auth | `hono/jwk` `jwk` | rejects `HS256/384/512`; asymmetric only |
| JWT Auth | `hono/jwt` `jwt` | `secret` and `alg` required; payload `c.get('jwtPayload')`; `verification.iss` not checked unless set; also `sign`, `verify`, `decode`, `verifyWithJwks` helpers |
| Language | `hono/language` `languageDetector` | |
| Logger | `hono/logger` `logger` | |
| Method Not Allowed | `hono/method-not-allowed` `methodNotAllowed({ app })` | 405 with `Allow` header when path matches but method does not |
| Method Override | `hono/method-override` `methodOverride` | |
| Mount | `hono/mount` `mount` | replaces `app.mount()` in v5 RC |
| Powered By | `hono/powered-by` `poweredBy` | |
| Pretty JSON | `hono/pretty-json` `prettyJSON` | |
| Request ID | `hono/request-id` `requestId` | |
| Secure Headers | `hono/secure-headers` `secureHeaders`, `NONCE` | CSP options; `NONCE` works with `hono/css` `<Style nonce>` |
| Server-Timing | `hono/timing` | verify import against docs |
| Timeout | `hono/timeout` `timeout(ms)` | custom exception factory (e.g. `HTTPException(408, ...)`) |
| Trailing Slash | `hono/trailing-slash` `trimTrailingSlash` | |

## Rules of thumb
- Register CORS before routes (and before auth when preflight must pass); use explicit origins.
- Create env-dependent middleware inside `app.use((c, next) => mw({ ...c.env... })(c, next))`.
- JWT: always pass `alg`. JWK: asymmetric algs only.
- CSRF does not protect JSON POSTs by itself; anchor origin regexes with `$`.

## Third-party (not bundled; https://github.com/honojs/middleware)
Auth: Auth.js, Casbin, Clerk, Cloudflare Access, OAuth Providers, OIDC Auth, Firebase Auth, Stytch (and others listed on the page). Validators: Zod (`@hono/zod-validator`), Ajv, ArkType, Class Validator, Conform, Effect Schema, Standard Schema (`@hono/standard-validator`), TypeBox, Typia. Review any third-party package before adding it.
