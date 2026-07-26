---
name: bun-backend
description: Use when building, reviewing, migrating, or troubleshooting JavaScript/TypeScript backends that intentionally use the Bun runtime, package manager, test runner, bundler, or Bun-native frameworks such as Elysia or BurgerAPI.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bun, javascript, typescript, backend, runtime, package-manager, test-runner, bundler, elysia, burgerapi]
    related_skills: [node-backend, api-governance, openapi-api-designer, graphql-api, code-performance-engineering, test-driven-development, requesting-code-review]
---

# Bun Backend

## Overview

Use this skill for backend work where Bun is a deliberate part of the stack: runtime, package manager, test runner, bundler, executable compiler, or framework platform. Bun can simplify TypeScript execution, dependency installation, tests, and builds, but it is not automatically a drop-in replacement for every Node.js production service. Start from the repository's current runtime and deployment constraints, then choose Bun-native APIs where they improve the project without breaking compatibility.

Pair with:
- `node-backend` for general backend architecture, validation, auth, database, logging, and service layering patterns that still apply to Bun services
- `api-governance`, `openapi-api-designer`, or `graphql-api` when the API contract itself is being designed or reviewed
- `code-performance-engineering` when performance claims, benchmark design, profiling, startup time, memory, throughput, or tail latency matter
- `test-driven-development` when adding behavior through RED-GREEN-REFACTOR
- `requesting-code-review` before publishing substantial backend changes

Linked references:
- `references/elysia.md` — default Bun-native framework reference for code-first APIs, plugins, validation, OpenAPI, testing, and WebSocket support
- `references/burgerapi.md` — secondary reference when file-based routing and convention-driven scaffolding are the main design goals

## When to Use

Use this skill when the task involves:

- Creating or modifying a Bun JavaScript/TypeScript backend
- Migrating package management, scripts, tests, or runtime execution from Node.js/npm/yarn/pnpm to Bun
- Using `bun install`, `bun run`, `bun test`, `bun build`, `bunx`, or Bun executable compilation
- Using Bun APIs such as `Bun.serve`, `Bun.file`, `Bun.write`, `Bun.password`, `bun:sqlite`, or `Bun.SQL`
- Choosing or working with Bun-native frameworks, especially Elysia or BurgerAPI
- Debugging Bun-specific module resolution, TypeScript, lockfile, runtime compatibility, test, bundling, or deployment issues
- Reviewing whether Bun is appropriate for a service currently built around Node.js, Express, Fastify, NestJS, Vite, or a serverless target

Do not use this skill as the only guide for:

- Generic Node.js backend work with no Bun-specific decisions; use `node-backend`
- Frontend-only React/Vue/Svelte work unless Bun is the package manager/build runner under discussion
- API contract design where runtime choice is incidental; use the relevant API skill first
- Infrastructure provisioning or container/platform work with no application-runtime decisions

## Core Principles

1. **Use Bun intentionally.** Prefer Bun where it simplifies runtime execution, test speed, package management, or deployment, not just because it is new.
2. **Keep backend architecture boring.** Routes/handlers should stay thin; services own business behavior; validation and errors are explicit.
3. **Verify Node compatibility instead of assuming it.** Most Node APIs and npm packages work, but native modules, runtime globals, test behavior, and bundling edges still need real checks.
4. **Prefer Bun-native tools when the repo commits to Bun.** Use `bun install`, `bun run`, `bun test`, `bun build`, and `bunx` consistently instead of mixing package managers without a reason.
5. **Treat install scripts as trust-boundary crossings.** Do not pipe remote installers into shells during automated work unless the user explicitly approves that install path.
6. **Measure performance claims.** Bun is fast, but production claims need benchmarks or traces relevant to the actual service.

## Discovery Checklist

Before changing a Bun project, inspect:

- `package.json` scripts and package manager assumptions
- `bun.lock`, `bun.lockb`, `package-lock.json`, `pnpm-lock.yaml`, or `yarn.lock`
- `bunfig.toml` if present
- `tsconfig.json`
- runtime entrypoints such as `src/index.ts`, `server.ts`, `app.ts`, or framework bootstrap files
- test files and whether they use `bun:test`, Jest, Vitest, or framework-specific harnesses
- deployment target: container, bare VM, serverless, edge, executable, or package artifact
- framework: raw `Bun.serve`, Elysia, Hono, Express/Fastify-on-Bun, BurgerAPI, or another stack

If multiple lockfiles exist, determine whether Bun is authoritative before running installs or changing dependencies.

## Installation and Tooling Safety

For this Hermes host, first check whether Bun already exists:

```bash
command -v bun && bun --version
```

If Bun is missing, prefer package-manager installation on macOS when available:

```bash
brew install oven-sh/bun/bun
```

Bun's official installer is commonly documented as:

```bash
curl -fsSL https://bun.com/install | bash
```

That command downloads and executes remote code. Treat it as a side-effecting install that requires explicit user approval in managed environments. If using it, first verify the official source and run it only in the intended user account/session.

Avoid global tool churn during project work unless needed. Prefer repository-local scripts and `bunx` for one-off package binaries.

## Project Setup Defaults

For a new Bun backend, prefer a simple, explicit structure:

```text
project/
  src/
    index.ts          # process entrypoint / listen
    app.ts            # app factory without listen side effects
    routes/           # route groups by domain
    services/         # business logic
    schemas/          # validation and response schemas
    plugins/          # framework plugins/context where applicable
    lib/              # adapters/utilities
  test/ or src/**/*.test.ts
  package.json
  tsconfig.json
  bun.lock
  README.md
```

Initialize or install with:

```bash
bun init
bun install
bun add <package>
bun add -d <dev-package>
bun remove <package>
bun update
bun outdated
```

Use one authoritative lockfile. Modern Bun projects commonly use `bun.lock`; older projects may have `bun.lockb`. Do not delete other lockfiles until you know the repo is migrating package managers.

## package.json and Scripts

A backend-oriented `package.json` usually has explicit scripts:

```json
{
  "type": "module",
  "scripts": {
    "dev": "bun --watch src/index.ts",
    "start": "bun src/index.ts",
    "test": "bun test",
    "build": "bun build src/index.ts --outdir dist --target bun",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "@types/bun": "latest",
    "typescript": "^5.0.0"
  }
}
```

Guidelines:

- Keep `typecheck` separate from `bun test`; Bun transpiles TypeScript but does not replace full static type checking.
- Use `bun run <script>` in automation for clarity, even though Bun supports shorthand such as `bun test` and `bun dev`.
- Do not mix `npm install` and `bun install` in the same repo unless the project intentionally supports both.

## TypeScript Defaults

For current Bun projects, prefer Bun's modern type package and module settings:

```json
{
  "compilerOptions": {
    "lib": ["ESNext"],
    "target": "ESNext",
    "module": "Preserve",
    "moduleDetection": "force",
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "noEmit": true,
    "strict": true,
    "skipLibCheck": true,
    "types": ["bun"]
  }
}
```

Notes:

- Prefer `@types/bun` / `types: ["bun"]` for current projects. Older projects may still use `bun-types`; migrate only when it is in scope.
- Keep `strict` enabled unless the repo has an explicit incremental migration plan.
- Use `tsc --noEmit` for type checks in CI when type safety matters.

## Runtime Patterns

### Raw Bun.serve

Use `Bun.serve` for small services, health endpoints, webhooks, internal tools, and cases where a framework is unnecessary:

```ts
const server = Bun.serve({
  port: Number(Bun.env.PORT ?? 3000),
  async fetch(request) {
    const url = new URL(request.url)

    if (url.pathname === '/health') {
      return Response.json({ ok: true })
    }

    return Response.json({ error: 'Not found' }, { status: 404 })
  },
  error(error) {
    console.error(error)
    return Response.json({ error: 'Internal server error' }, { status: 500 })
  }
})

console.log(`Listening on ${server.url}`)
```

For non-trivial APIs, use a framework or a small routing layer rather than hand-rolling every route.

### Elysia as default framework reference

Use Elysia when you want Bun-native routing, TypeScript-first ergonomics, schema validation, plugins, OpenAPI, and testable app factories. See `references/elysia.md`.

### BurgerAPI as file-routing reference

Use BurgerAPI when file-based routing and convention-driven scaffolding are intentionally part of the architecture. See `references/burgerapi.md`.

## Environment and Configuration

Bun automatically loads `.env` files for typical runtime use. Do not add `dotenv` unless the project has a specific compatibility reason.

Guidelines:

- Read config through `Bun.env` or `process.env` consistently.
- Validate required config at startup with a schema or small config module.
- Never commit `.env` files with real secrets.
- Add `.env.example` for required keys.
- Redact secrets from logs and test output.

Example:

```ts
const config = {
  port: Number(Bun.env.PORT ?? 3000),
  databaseUrl: Bun.env.DATABASE_URL
}

if (!config.databaseUrl) {
  throw new Error('DATABASE_URL is required')
}
```

## Testing with bun:test

Use `bun:test` for Bun-native projects unless the repo already depends on Jest/Vitest features that are not worth migrating.

```ts
import { describe, expect, it } from 'bun:test'
import { app } from '../src/app'

describe('health', () => {
  it('returns ok', async () => {
    const response = await app.fetch(new Request('http://localhost/health'))
    expect(response.status).toBe(200)
    await expect(response.json()).resolves.toEqual({ ok: true })
  })
})
```

Testing guidance:

- Export an app/fetch handler without listening so tests do not need real ports.
- Keep unit tests close to services and integration tests close to HTTP behavior.
- Use `bun test --coverage` when coverage is part of the quality gate.
- Run type checks separately with `bun run typecheck` or `tsc --noEmit`.
- For database tests, isolate state and clean up files/containers after tests.

## Bundling, Build, and Executables

Use `bun build` for bundling services, CLIs, and browser/server artifacts:

```bash
bun build src/index.ts --outdir dist --target bun
```

For standalone CLIs or deployment artifacts, Bun can compile executables:

```bash
bun build src/cli.ts --compile --outfile dist/my-tool
```

Build guidance:

- Set the correct target: `bun`, `node`, or browser depending on where the artifact runs.
- Decide whether `.env`/`bunfig` should be auto-loaded in compiled executables.
- Keep source maps when production debugging matters.
- Verify the built artifact by running it, not just by checking that `bun build` exits zero.

## Data and Built-in APIs

Useful Bun-native APIs:

- `Bun.file` and `Bun.write` for efficient file reads/writes
- `Bun.serve` for HTTP and WebSocket servers
- `Bun.password` for password hashing and verification
- `bun:sqlite` or `Bun.SQL` for SQLite-backed local apps or tests
- standard `fetch`, `Request`, `Response`, `WebSocket`, and Web Streams APIs

Security notes:

- Use appropriate password hashing algorithm/cost for the production threat model; do not rely on defaults blindly for security-sensitive systems.
- Avoid logging request bodies, secrets, auth headers, or connection strings.
- Treat SQLite file paths and uploaded-file paths as filesystem trust boundaries.

## Migration from Node.js

Migration workflow:

1. Inventory scripts, dependencies, lockfiles, native modules, and deployment target.
2. Add Bun locally and run existing tests without changing code where possible.
3. Switch package installation only after deciding Bun is the package manager of record.
4. Update scripts incrementally: test, dev, start, build.
5. Replace Node-specific tooling only when Bun has a proven equivalent for the repo.
6. Run integration tests and deployment smoke tests before removing Node-era files.

Compatibility checks:

- Native dependencies and postinstall scripts
- CJS/ESM edge cases and dynamic require/import behavior
- test runner APIs and mocking behavior
- framework adapters and serverless targets
- bundling assumptions around externals, assets, and environment variables

Do not claim a migration is complete until the actual test/build/start commands pass under Bun.

## Performance Review

Bun often improves install speed, startup time, test time, and simple HTTP throughput, but performance changes should be evidence-backed.

When performance matters, capture:

- baseline command timings before and after migration
- p50/p95/p99 HTTP latency under representative load
- memory and CPU behavior under expected concurrency
- cold start time if used in serverless or CLI contexts
- package install time only if dependency workflow is part of the goal

Pair with `code-performance-engineering` for benchmark design and regression guardrails.

## Suggested Workflow

1. Confirm Bun is installed and record `bun --version` when environment behavior matters.
2. Inspect package manager, lockfiles, scripts, TypeScript config, and framework.
3. Decide whether the work is runtime, package-manager, test, build, framework, or migration focused.
4. Make the smallest coherent change.
5. Run the relevant real commands: `bun install`, `bun run typecheck`, `bun test`, `bun run build`, and/or a service smoke test.
6. For API changes, verify endpoint behavior through HTTP-level tests or direct `fetch`/framework handlers.
7. Report exact commands run and outcomes.

## Common Pitfalls

1. **Piping remote installers into a shell without approval.** Use Homebrew or ask first for installer-script use.
2. **Assuming Bun transpilation equals type safety.** Run `tsc --noEmit` for type checks.
3. **Mixing package managers accidentally.** Multiple lockfiles can create non-reproducible dependency state.
4. **Assuming every Node package is production-safe on Bun.** Verify native modules, test runners, and runtime APIs.
5. **Putting business logic in route handlers.** Bun does not remove the need for service/domain boundaries.
6. **Skipping deployment smoke tests.** Build success does not prove the target platform can run the artifact.
7. **Overusing raw `Bun.serve`.** For larger APIs, a framework or routing layer improves validation, errors, docs, and tests.
8. **Logging secrets through automatic `.env` loading.** Validate config and redact sensitive values.
9. **Benchmarking only the happy path.** Include representative payloads, database calls, concurrency, and tail latency.
10. **Treating generated OpenAPI as automatically good.** Review it as an API contract.

## Verification Checklist

- [ ] Bun is intentionally part of the stack and the relevant Bun version is known when needed
- [ ] Package manager and lockfile ownership are clear
- [ ] `package.json` scripts use Bun consistently where appropriate
- [ ] TypeScript config uses current Bun types or preserves the repo's intentional legacy setup
- [ ] Type checking is run separately when type safety matters
- [ ] Tests run through `bun test` or the repo's explicit test runner
- [ ] Build/compile artifacts are executed or smoke-tested after creation
- [ ] Runtime APIs and Node compatibility assumptions are verified with real commands
- [ ] API handlers keep validation, errors, and business logic cleanly separated
- [ ] Environment variables and secrets are validated and not logged
- [ ] Elysia/BurgerAPI/framework docs are paired when framework-specific decisions matter
