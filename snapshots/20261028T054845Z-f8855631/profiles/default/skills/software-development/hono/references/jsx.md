# JSX

Sources: https://hono.dev/docs/guides/jsx, https://hono.dev/docs/guides/jsx-dom, https://hono.dev/docs/middleware/builtin/jsx-renderer (in https://hono.dev/llms-full.txt).

## Setup
- `tsconfig.json`: `{"compilerOptions":{"jsx":"react-jsx","jsxImportSource":"hono/jsx"}}`; or pragmas `/** @jsx jsx */` + `/** @jsxImportSource hono/jsx */`.
- Deno: `deno.json` `{"compilerOptions":{"jsx":"precompile","jsxImportSource":"@hono/hono/jsx"}}`. (`useRequestContext()` does not work with Deno `precompile`; use `react-jsx`.)
- Files must be `.tsx`.

## Server features (hono/jsx)
- `PropsWithChildren`, `Fragment`, `memo`, context (`createContext`/`useContext`), `dangerouslySetInnerHTML={{ __html }}` (raw; never with untrusted input).
- Metadata hoisting: `<title>`, `<link>`, `<meta>` in components are hoisted to `<head>`; existing head elements are not removed and later ones are appended.
- Async components work with `c.html()` (awaited). `Suspense`, `ErrorBoundary`, `StreamingContext` are labelled **Experimental**; used with `renderToReadableStream()`.
- Integrates with `html` helper and `jsxRenderer`.

## jsxRenderer (`hono/jsx-renderer`)
- `app.use(jsxRenderer(({ children }) => <html>...</html>, options))`, then `c.render(<X />)`. Options: `docType` (boolean | string), `stream` (boolean | Record), function-based options (e.g. disable streaming for SSG with `isSSGContext`). Nested layouts supported; `useRequestContext()` returns the Context; extend `ContextRenderer` for typed props.

## Client components (hono/jsx/dom)
- `render(<App />, container)` from `hono/jsx/dom`; React-compatible hooks (`useState`, `useEffect`, `useRef`, `useCallback`, `useMemo`, `useReducer`, `useId`, `useTransition`, ... full list on the page), `startViewTransition` family.
- Smaller runtime: `jsxImportSource: "hono/jsx/dom"` (tsconfig, or esbuild option in `vite.config.ts`).
