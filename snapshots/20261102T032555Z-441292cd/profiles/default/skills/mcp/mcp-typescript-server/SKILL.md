---
name: mcp-typescript-server
description: "Use when building, scaffolding, or reviewing an MCP server using the official TypeScript SDK (v2). Covers McpServer registration (tools, resources, prompts), stdio and Streamable HTTP transports, framework integration, sessions/scaling, security, testing, and v1→v2 migration."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mcp, typescript, node, server, sdk, streamable-http, stdio, zod]
    related_skills: [native-mcp, fastmcp-http-python-docker-server, mcpjam-inspector, aws-mcp-setup]
---

# MCP TypeScript Server Authoring

## Overview

This skill covers authoring MCP servers with the official **`@modelcontextprotocol/server`** TypeScript SDK **v2**, the stable release line implementing the **2026-07-28 MCP specification**. v1.x continues to receive bug fixes but v2 is the active development line.

The SDK runs on Node.js, Bun, and Deno. Tool and prompt schemas use **Standard Schema** — bring Zod v4, Valibot, ArkType, or any compatible library. Zod v4 (`zod/v4`) is the default in all examples here.

A complete MCP server is one file:

```ts
import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';

serveStdio(() => {
    const server = new McpServer({ name: 'weather', version: '1.0.0' });

    server.registerTool(
        'get-forecast',
        {
            description: 'Get the weather forecast for a city',
            inputSchema: z.object({ city: z.string() })
        },
        async ({ city }) => ({
            content: [{ type: 'text', text: `Sunny in ${city} all week.` }]
        })
    );

    return server;
});
```

## When to Use

- Building a new MCP server in TypeScript/Node.js (Bun or Deno also work)
- Scaffolding a server project with proper package layout, transports, and tests
- Registering tools, resources, or prompts with the v2 SDK API
- Choosing between stdio and Streamable HTTP transports
- Integrating MCP into an existing Express, Hono, Fastify, or Cloudflare Workers app
- Implementing sessionful or stateless HTTP serving, scaling across nodes
- Migrating a v1 server to v2 (`tool()` → `registerTool`, etc.)
- Reviewing an MCP server codebase for SDK correctness and security

Don't use for:
- Configuring Hermes' native MCP *client* — use `native-mcp` for that
- Python/FastMCP servers — use `fastmcp-http-python-docker-server`
- Protocol conformance testing or security review — use `mcpjam-inspector`

## Prerequisites

- **Node.js** 18+ (or Bun 1.0+, or Deno 1.40+)
- **TypeScript** 5.0+
- **Zod v4** (`zod/v4`) or another Standard Schema-compatible library
- Install the server package: `npm install @modelcontextprotocol/server`

## Project Scaffold

### Package layout

```
my-mcp-server/
├── package.json
├── tsconfig.json
├── src/
│   └── index.ts          # entry: serveStdio(createServer) or HTTP handler
├── scripts/
│   ├── run-stdio.sh      # local stdio launch
│   └── run-http.sh       # local HTTP launch
├── tests/
│   └── server.test.ts    # in-memory Client tests
└── README.md
```

### package.json (essentials)

```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start:stdio": "node dist/index.js",
    "start:http": "node dist/http.js",
    "test": "vitest run"
  },
  "dependencies": {
    "@modelcontextprotocol/server": "^2.0.0",
    "zod": "^3.25.0"
  },
  "devDependencies": {
    "@modelcontextprotocol/client": "^2.0.0",
    "typescript": "^5.5.0",
    "vitest": "^2.0.0"
  }
}
```

> **Zod v4 import:** `import * as z from 'zod/v4'` — the `/v4` subpath is required even when the `zod` package is at v3.25+. The SDK's Standard Schema integration reads Zod v4 schemas.

### tsconfig.json (essentials)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "dist",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

### Factory pattern

Always wrap server creation in a factory function. This is mandatory for HTTP serving (the handler builds a fresh instance per request) and recommended for stdio (keeps the entry cheap and testable):

```ts
function createServer(): McpServer {
    const server = new McpServer({ name: 'my-server', version: '1.0.0' });
    // register tools, resources, prompts here
    return server;
}
```

Keep the factory **cheap and side-effect-free**: create connection pools, caches, and shared clients once at module scope and close over them — never inside the factory.

## Tools

### Register a tool

`registerTool(name, config, handler)` — the only schema you write is `inputSchema` (a Zod object). The SDK derives the JSON Schema the model sees, validates arguments before the handler runs, and infers handler argument types.

```ts
server.registerTool(
    'search',
    {
        description: 'Search the product catalog',
        inputSchema: z.object({
            query: z.string().describe('Substring to match against product names'),
            limit: z.number().int().max(50).optional()
        })
    },
    async ({ query, limit }) => {
        const hits = catalog.filter(p => p.name.toLowerCase().includes(query.toLowerCase()));
        const names = hits.slice(0, limit ?? 10).map(p => p.name);
        return { content: [{ type: 'text', text: names.join('\n') }] };
    }
);
```

`.describe()` on schema fields survives the Zod → JSON Schema conversion — it becomes the `description` the model sees in `tools/list`. This is the only documentation the model gets for that argument.

### Tool with no arguments

Omit `inputSchema` entirely:

```ts
server.registerTool(
    'clear-catalog',
    {
        title: 'Clear the catalog',
        description: 'Remove every product from the catalog',
        annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: true }
    },
    async () => {
        catalog.length = 0;
        return { content: [{ type: 'text', text: 'Catalog cleared' }] };
    }
);
```

`title` is the display name; `annotations` are behavior hints the client uses (e.g. auto-approve read-only tools, require confirmation for destructive ones). Annotations never change how the SDK runs the tool.

### Structured output

Add `outputSchema` and return `structuredContent` alongside the human-readable `content`:

```ts
server.registerTool(
    'product-details',
    {
        description: 'Look up one product by its exact name',
        inputSchema: z.object({ name: z.string() }),
        outputSchema: z.object({ name: z.string(), price: z.number() })
    },
    async ({ name }) => {
        const product = catalog.find(c => c.name === name);
        if (!product) throw new Error(`No product named ${name}`);
        const output = { name: product.name, price: product.price };
        return {
            content: [{ type: 'text', text: JSON.stringify(output) }],
            structuredContent: output
        };
    }
);
```

The SDK validates `structuredContent` against `outputSchema` before the result leaves the server and advertises the derived JSON Schema in `tools/list`.

### Error handling in tool handlers

- **Argument validation failure:** the SDK rejects it before the handler runs — returns `{ content: [{ type: 'text', text: 'Input validation error: ...' }], isError: true }`. The model reads the message and retries.
- **Handler throws or returns `isError: true`:** the result comes back to the client as an `isError: true` tool result. Use this for application-level failures (API down, not found).
- **Protocol-level failures:** thrown errors that aren't caught are protocol errors. See the Errors page in the v2 docs.

### Content types in tool results

The `content` array accepts:

- `{ type: 'text', text: string }`
- `{ type: 'image', data: string, mimeType: string }` — base64-encoded
- `{ type: 'audio', data: string, mimeType: string }` — base64-encoded
- `{ type: 'resource_link', uri: string, name?: string, mimeType?: string }`
- `{ type: 'resource', resource: { uri: string, mimeType?: string, text?: string, blob?: string } }`

## Resources

Resources are **application-controlled** read-only data (files, database rows, rendered reports). The client decides what to read, unlike tools which are model-controlled.

### Static resource

```ts
import { McpServer, ResourceTemplate } from '@modelcontextprotocol/server';

server.registerResource(
    'config',
    'config://app',
    {
        title: 'Application Config',
        description: 'Application configuration data',
        mimeType: 'text/plain'
    },
    async (uri) => ({
        contents: [{ uri: uri.href, text: 'log_level=info\nregion=eu-west-1' }]
    })
);
```

### Resource template (URI pattern)

```ts
server.registerResource(
    'user-profile',
    new ResourceTemplate('users://{userId}/profile', { list: undefined }),
    {
        title: 'User Profile',
        description: 'Profile data for one user',
        mimeType: 'application/json'
    },
    async (uri, { userId }) => ({
        contents: [{ uri: uri.href, mimeType: 'application/json', text: JSON.stringify({ userId, plan: 'pro' }) }]
    })
);
```

Matched variables arrive parsed as the read callback's second argument. Pass `list: undefined` when instances are unbounded; pass a `list` callback when the set is enumerable:

```ts
new ResourceTemplate('teams://{teamId}/roster', {
    list: async () => ({
        resources: [
            { uri: 'teams://core/roster', name: 'Core team roster' },
            { uri: 'teams://growth/roster', name: 'Growth team roster' }
        ]
    })
})
```

### Resource contents

The read callback returns `{ contents: [...] }`. Each item carries either `text` or a base64 `blob`, plus `uri` and optional `mimeType`:

```ts
async (uri) => ({
    contents: [
        { uri: uri.href, mimeType: 'text/markdown', text: 'Report text...' },
        { uri: uri.href, mimeType: 'image/png', blob: base64PngString }
    ]
})
```

### File-backed path sanitization

When a template variable becomes a filesystem path, resolve and constrain it:

```ts
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

server.registerResource(
    'file',
    new ResourceTemplate('file:///{+path}', { list: undefined }),
    { description: 'Read a file from the workspace root', mimeType: 'text/plain' },
    async (uri, { path }) => {
        const root = resolve(WORKSPACE_ROOT);
        const requested = resolve(root, decodeURIComponent(path));
        if (!requested.startsWith(root)) {
            throw new Error('Path traversal rejected');
        }
        const text = await fs.readFile(requested, 'utf-8');
        return { contents: [{ uri: uri.href, text }] };
    }
);
```

## Prompts

Prompts are **user-controlled** message templates surfaced as slash commands or menu entries. The client picks a prompt; the model picks tools.

### Register a prompt

```ts
import { McpServer } from '@modelcontextprotocol/server';
import * as z from 'zod/v4';

server.registerPrompt(
    'review-code',
    {
        title: 'Code Review',
        description: 'Review code for best practices and potential issues',
        argsSchema: z.object({
            code: z.string().describe('The code to review')
        })
    },
    ({ code }) => ({
        messages: [
            {
                role: 'user' as const,
                content: { type: 'text' as const, text: `Review this code:\n\n${code}` }
            }
        ]
    })
);
```

`argsSchema` is a Zod object schema. A failed prompt validation is a protocol error (`-32602`), unlike tool argument rejection which comes back as `isError: true`.

### Multi-message prompts

Include an `assistant` message to seed how the model's reply starts:

```ts
({ error }) => ({
    messages: [
        { role: 'user' as const, content: { type: 'text' as const, text: `Explain this compiler error:\n\n${error}` } },
        { role: 'assistant' as const, content: { type: 'text' as const, text: 'The one-line cause:' } }
    ]
})
```

### Embed a resource in a prompt message

```ts
({ code }) => ({
    messages: [
        {
            role: 'user' as const,
            content: {
                type: 'resource' as const,
                resource: { uri: 'doc://style-guide', mimeType: 'text/markdown', text: styleGuideText }
            }
        },
        {
            role: 'user' as const,
            content: { type: 'text' as const, text: `Review this code against the style guide:\n\n${code}` }
        }
    ]
})
```

`content` accepts: `text`, `image`, `audio`, `resource_link`, and `resource`.

## Transports

### stdio

For local servers launched as child processes by an MCP host:

```ts
import { serveStdio } from '@modelcontextprotocol/server/stdio';

void serveStdio(createServer);
console.error('MCP server running on stdio');
```

`serveStdio` takes a factory and handles the transport lifecycle. Use `console.error` for logs — stdout is reserved for MCP protocol messages.

### Streamable HTTP (stateless default)

For remote/shared servers. `createMcpHandler(factory)` returns a web-standard handler:

```ts
import { createMcpHandler, McpServer } from '@modelcontextprotocol/server';
import * as z from 'zod/v4';

const handler = createMcpHandler(() => {
    const server = new McpServer({ name: 'notes', version: '1.0.0' });
    server.registerTool('add-note', {
        description: 'Save a note',
        inputSchema: z.object({ text: z.string() })
    }, async ({ text }) => ({ content: [{ type: 'text', text: `Saved: ${text}` }] }));
    return server;
});

// handler.fetch is a web-standard (Request) => Promise<Response>
// handler.close for shutdown
// handler.notify / handler.bus for change notifications
```

**Per-request factory:** the factory runs once per HTTP request — a fresh `McpServer` instance serves every request. The handler holds nothing between requests. Register tools, resources, and prompts *inside* the factory, never on a shared instance outside it.

The factory receives the request context: `{ era, authInfo, requestInfo }`:

```ts
const perCaller = createMcpHandler(({ authInfo }) => {
    const server = new McpServer({ name: 'notes', version: '1.0.0' });
    server.registerTool('whoami', { description: 'Name the authenticated caller' }, async () => ({
        content: [{ type: 'text', text: authInfo?.clientId ?? 'anonymous' }]
    }));
    return server;
});
```

### Mounting on runtimes

| Runtime | How to mount |
|---|---|
| Cloudflare Workers, Deno, Bun | `export default handler` |
| Node.js (`node:http`) | `toNodeHandler(handler)` from `@modelcontextprotocol/node` + `localhostHostValidation` / `localhostOriginValidation` guards |
| Express | `createMcpExpressApp(handler)` from `@modelcontextprotocol/express` — both validations armed by default |
| Hono | `createMcpHonoApp(handler)` from `@modelcontextprotocol/hono` |
| Fastify | `createMcpFastifyApp(handler)` from `@modelcontextprotocol/fastify` |

On plain `node:http`, bind to loopback explicitly and compose the Host/Origin validation guards:

```ts
import { toNodeHandler } from '@modelcontextprotocol/node';
import { localhostHostValidation, localhostOriginValidation } from '@modelcontextprotocol/node';
import { createServer } from 'http';

const nodeHandler = toNodeHandler(handler.fetch);
const server = createServer((req, res) => {
    // Host validation first (DNS rebinding defense)
    const hostGuard = localhostHostValidation(req);
    if (hostGuard) { res.writeHead(403).end(); return; }
    const originGuard = localhostOriginValidation(req);
    if (originGuard) { res.writeHead(403).end(); return; }
    nodeHandler(req, res);
});

server.listen(3000, '127.0.0.1');
```

## Security

### Host and Origin validation

The handler trusts its caller — it validates no `Host` or `Origin` header. Mount these checks **in front** of it:

- **DNS rebinding defense:** on localhost binds, the `Host` check stops a malicious page from resolving its domain to `127.0.0.1` and treating your local server as same-origin.
- Framework adapters (`createMcpExpressApp`, `createMcpHonoApp`, `createMcpFastifyApp`) arm both validations by default on localhost binds.
- On bare fetch runtimes, use `hostHeaderValidationResponse` and `originValidationResponse` from `@modelcontextprotocol/server` in front of `handler.fetch`.

### Authentication

`authInfo` is **pass-through**: the handler never reads it from headers and never verifies a token. Verify the bearer token in front of the handler and pass the result via `fetch`'s second argument. Destructure `authInfo` inside the factory to build per-caller instances.

### Secrets

- Keep secrets out of source — use environment variables.
- Never hardcode API keys in code or examples.
- Raise clear errors for missing env vars and upstream HTTP failures.

## Sessions, State, and Scaling

### Stateless (v2 default)

`createMcpHandler` builds a fresh instance per request and holds nothing between requests. The endpoint is **stateless and scales horizontally** — put nodes behind any load balancer, no session affinity needed.

### Sessionful (2025-era transport)

Sessions belong to the hand-wired `NodeStreamableHTTPServerTransport` (2025-era). The 2026-07-28 revision is per-request and has no `Mcp-Session-Id`.

```ts
import { NodeStreamableHTTPServerTransport } from '@modelcontextprotocol/node';
import { randomUUID } from 'node:crypto';

const transport = new NodeStreamableHTTPServerTransport({
    sessionIdGenerator: () => randomUUID()
});
```

A sessionful deployment keeps a `Map<string, NodeStreamableHTTPServerTransport>`, builds a transport on `initialize`, stores it in `onsessioninitialized`, and routes later requests by `Mcp-Session-Id`. See the v2 docs "Sessions, state, and scaling" page for the full Express route handler.

### Stream resumability

Configure an `EventStore` (two-method contract: `storeEvent` + `replayEventsAfter`) over shared storage. The transport stamps SSE messages with event IDs; clients reconnect with `Last-Event-ID` and the transport replays missed events. `examples/shared/src/inMemoryEventStore.ts` in the SDK repo is a reference implementation (in memory, single-process only).

### Cross-node scaling

The stateless default needs no shared state. For cross-node `subscriptions/listen` notifications, implement `ServerEventBus` over your pub/sub and pass it to `createMcpHandler`:

```ts
const handler = createMcpHandler(buildServer, { bus: redisBus });
```

## Testing

Use an in-memory `Client` from `@modelcontextprotocol/client` to drive tool/resource/prompt calls without a real transport:

```ts
import { Client } from '@modelcontextprotocol/client';
import { test, expect } from 'vitest';

test('search tool returns results', async () => {
    const client = new Client({ name: 'test-client', version: '1.0.0' });
    // Connect client to server in-memory (see v2 "Testing" guide)
    
    const result = await client.callTool({ name: 'search', arguments: { query: 'mug' } });
    expect(result.content).toEqual([{ type: 'text', text: 'Travel mug\nMug rack' }]);
    
    // Schema rejection
    const rejected = await client.callTool({ name: 'search', arguments: { query: 'mug', limit: 999 } });
    expect(rejected.isError).toBe(true);
});
```

## v1 → v2 Migration

| v1 | v2 |
|---|---|
| `server.tool(name, ...)` | `server.registerTool(name, config, handler)` |
| `server.resource(name, ...)` | `server.registerResource(name, uri, config, readCallback)` |
| `server.prompt(name, ...)` | `server.registerPrompt(name, config, callback)` |
| `StreamableHTTPServerTransport` + `connect()` | `createMcpHandler(factory)` |
| `McpServer` shared instance | Factory pattern, fresh instance per request |
| Zod v3 | `zod/v4` (Standard Schema) |

Run the official codemod first, then review the upgrade guide at `https://ts.sdk.modelcontextprotocol.io/v2/migration/upgrade-to-v2`.

## Packages

The SDK is a monorepo with split packages:

| Package | Purpose |
|---|---|
| `@modelcontextprotocol/server` | Build MCP servers (core) |
| `@modelcontextprotocol/client` | Build MCP clients (for testing or client apps) |
| `@modelcontextprotocol/node` | Node.js-specific transports and helpers (`toNodeHandler`, `localhostHostValidation`, `NodeStreamableHTTPServerTransport`) |
| `@modelcontextprotocol/express` | Express middleware adapter |
| `@modelcontextprotocol/hono` | Hono adapter |
| `@modelcontextprotocol/fastify` | Fastify adapter |

## Common Pitfalls

1. **Importing `zod` instead of `zod/v4`.** The SDK's Standard Schema integration requires the `/v4` subpath: `import * as z from 'zod/v4'`. Using bare `zod` will not produce compatible schemas.

2. **Registering tools outside the factory.** In HTTP mode, the factory runs per request. Tools registered on a shared instance outside the factory won't be served. Always register inside the factory function.

3. **Using `console.log` on stdio transport.** stdout is reserved for MCP protocol messages. Use `console.error` for diagnostic output.

4. **Skipping Host/Origin validation on localhost HTTP.** Without the Host check, a malicious page can DNS-rebind to `127.0.0.1` and treat your local server as same-origin. Use the framework adapters (which arm both by default) or compose the guards manually.

5. **Treating `authInfo` as server-verified.** The handler never verifies tokens. Verify in front of the handler and pass the result through `authInfo`.

6. **Assuming v2 has `Mcp-Session-Id`.** The 2026-07-28 revision is per-request and stateless. Sessions are a 2025-era transport feature via `NodeStreamableHTTPServerTransport`.

7. **Using `tool()` / `resource()` / `prompt()` (v1 API).** These are removed in v2. Use `registerTool`, `registerResource`, `registerPrompt`.

8. **Creating expensive resources inside the factory.** The factory runs per HTTP request. Create connection pools, API clients, and caches at module scope and close over them.

9. **Not sanitizing file-backed resource paths.** When a `ResourceTemplate` variable maps to a filesystem path, resolve and constrain it to the workspace root before reading.

10. **Forgetting `outputSchema` validation.** When returning `structuredContent`, the SDK validates it against `outputSchema` before sending. If the output doesn't match, the result is rejected.

## Verification Checklist

- [ ] `npm install @modelcontextprotocol/server` and `zod` succeed
- [ ] `import * as z from 'zod/v4'` resolves (not bare `zod`)
- [ ] All tools/resources/prompts are registered inside the factory function
- [ ] stdio entry uses `serveStdio(createServer)` (not `server.connect()` directly)
- [ ] HTTP entry uses `createMcpHandler(factory)` with Host/Origin validation in front
- [ ] No secrets in source; env vars used for API keys
- [ ] Tool argument validation works (rejected args return `isError: true`)
- [ ] `structuredContent` matches `outputSchema` when used
- [ ] File-backed resource templates sanitize and constrain paths
- [ ] Tests use in-memory `Client` from `@modelcontextprotocol/client`
- [ ] `console.error` used for logs on stdio (not `console.log`)
- [ ] Project builds with `tsc` and runs with `node dist/index.js`

## Key References

- **v2 docs home:** `https://ts.sdk.modelcontextprotocol.io/v2/`
- **GitHub:** `https://github.com/modelcontextprotocol/typescript-sdk`
- **MCP spec (2026-07-28):** `https://modelcontextprotocol.io/specification/2026-07-28`
- **Examples:** `https://github.com/modelcontextprotocol/typescript-sdk/tree/main/examples`
- **v1 docs (legacy):** `https://ts.sdk.modelcontextprotocol.io/`
- For the compact API surface cheat sheet, see `references/v2-api-quick-reference.md`
