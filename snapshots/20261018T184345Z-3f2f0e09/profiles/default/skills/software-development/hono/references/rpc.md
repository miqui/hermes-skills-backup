# RPC client

Source: https://hono.dev/docs/guides/rpc (in https://hono.dev/llms-full.txt).

- Server: export `typeof app` (or route chain) as `AppType`. Client: `hc<AppType>('http://localhost:8787/')`; call `client.posts.$get({ query })`, `.$post({ json | form })`, path params `client.posts[':id'].$get({ param: { id } })`. Response is a fetch `Response`.
- Monorepo: `"strict": true` in both client and server tsconfig. Keep identical Hono versions on both sides (mismatch breaks inference). Routes must be chained.
- Cookies: `hc(url, { init: { credentials: 'include' } })`. `init` (a `RequestInit`) has highest priority and can override method/body/headers; use it for e.g. abort signals.
- Status codes: explicit status in `c.json(data, 404)` becomes part of the type; narrow with `res.status`/`res.ok`; `InferResponseType<typeof client.x.$get, 200>`; `InferRequestType`.
- Global error responses (`app.onError`, global middleware) are not inferred; `ApplyGlobalResponse<typeof app, { 500: { json: { error: string } } }>` from `hono/client`.
- `$url()` returns a `URL`; needs an **absolute** base URL (`hc('/')` throws). `$path()` returns the path (with `query`).
- File upload: pass `form: { file: new File(...) }`; server `zValidator('form', z.object({ file: z.instanceof(File) }))`.
- `parseResponse(client.hello.$get())` from `hono/client` parses by Content-Type and throws `DetailedError` when not ok.
- Also documented on the page: custom `fetch`, custom query serializer (`buildSearchParams`), SWR usage, splitting large apps with `app.route()`.
- Performance (IDE slowdown with many routes): match Hono versions, use TypeScript project references, precompute the client type (`const client = hc<typeof app>(''); export type Client = typeof client; export const hcWithType = (...args: Parameters<typeof hc>): Client => hc<typeof app>(...args)`), specify route type args manually, split app and client files.
