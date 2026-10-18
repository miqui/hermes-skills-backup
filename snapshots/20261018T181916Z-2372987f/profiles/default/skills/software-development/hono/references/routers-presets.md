# Routers and presets

Sources: https://hono.dev/docs/api/routing, https://hono.dev/docs/concepts/routers, https://hono.dev/docs/api/presets (all in https://hono.dev/llms-full.txt).

## Routers (Hono has five)
- **RegExpRouter**: compiles all routes into one regular expression; fastest, but does not support every pattern, so it is normally combined with another router.
- **TrieRouter**: trie-based; supports all patterns; slower than RegExpRouter, faster than the Express router.
- **SmartRouter**: picks the fastest router that supports the registered routes at startup. Default: `new SmartRouter({ routers: [new RegExpRouter(), new TrieRouter()] })`.
- **LinearRouter**: very fast route registration; for environments initialized on every request.
- **PatternRouter**: smallest (docs: app under 15KB).

## Presets (same `Hono` class, different router)
| Import | Router | Use |
| --- | --- | --- |
| `hono` | SmartRouter[RegExpRouter, TrieRouter] | Recommended default; long-lived servers (Deno, Bun, Node.js) |
| `hono/quick` | SmartRouter[LinearRouter, TrieRouter] | Initialized on every request |
| `hono/tiny` | PatternRouter | Resource-constrained environments, smallest |

Presets are interchangeable. Fastly Compute: with top-level `fire`, use `hono`, not `hono/quick` (see `runtimes.md`).

## Routing gotchas (from the routing/app docs)
- Registration order matters; HEAD is converted to GET before matching (`app.head()` never runs); strict mode default (`/hello` != `/hello/`, `strict: false` to relax); `app.notFound()` only on the top-level app; route-level `onError` beats parent. Verify exact wording in https://hono.dev/docs/api/routing and https://hono.dev/docs/api/hono.
