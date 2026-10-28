# MCP TypeScript SDK v2 API Quick Reference

> SDK version: `@modelcontextprotocol/server` v2.x, targeting MCP 2026-07-28 spec.
> Schema library: Zod v4 (`zod/v4`) by default; any Standard Schema-compatible library works.

## Imports

```ts
// Server core
import { McpServer, ResourceTemplate, createMcpHandler } from '@modelcontextprotocol/server';

// stdio transport
import { serveStdio } from '@modelcontextprotocol/server/stdio';

// Node.js-specific (transports, guards, helpers)
import { toNodeHandler, NodeStreamableHTTPServerTransport, localhostHostValidation, localhostOriginValidation } from '@modelcontextprotocol/node';

// Framework adapters
import { createMcpExpressApp } from '@modelcontextprotocol/express';
import { createMcpHonoApp } from '@modelcontextprotocol/hono';
import { createMcpFastifyApp } from '@modelcontextprotocol/fastify';

// Client (for testing)
import { Client } from '@modelcontextprotocol/client';

// Schema
import * as z from 'zod/v4';
```

## McpServer

```ts
const server = new McpServer({
    name: 'my-server',
    version: '1.0.0'
});
```

## registerTool

```ts
server.registerTool(
    name: string,
    config: {
        description: string;
        title?: string;
        inputSchema?: ZodObject;      // omit for no-arg tools
        outputSchema?: ZodObject;     // for structured output
        annotations?: {
            readOnlyHint?: boolean;
            destructiveHint?: boolean;
            idempotentHint?: boolean;
            openWorldHint?: boolean;
        };
    },
    handler: (args, extra) => Promise<{
        content: ContentBlock[];
        structuredContent?: unknown;   // must match outputSchema
        isError?: boolean;
    }>
);
```

### Content block types

```ts
{ type: 'text', text: string }
{ type: 'image', data: string, mimeType: string }   // base64
{ type: 'audio', data: string, mimeType: string }   // base64
{ type: 'resource_link', uri: string, name?: string, mimeType?: string }
{ type: 'resource', resource: { uri: string, mimeType?: string, text?: string, blob?: string } }
```

## registerResource

### Static resource

```ts
server.registerResource(
    name: string,
    uri: string,                    // fixed URI, e.g. 'config://app'
    config: {
        title?: string;
        description?: string;
        mimeType?: string;
    },
    readCallback: (uri: URL) => Promise<{
        contents: ResourceContent[];
    }>
);
```

### Resource template

```ts
server.registerResource(
    name: string,
    template: ResourceTemplate,     // URI pattern, e.g. 'users://{userId}/profile'
    config: { ... },
    readCallback: (uri: URL, vars: Record<string, string>) => Promise<{
        contents: ResourceContent[];
    }>
);
```

### ResourceTemplate construction

```ts
new ResourceTemplate('users://{userId}/profile', {
    list: undefined                          // unbounded set
    // OR
    list: async () => ({ resources: [{ uri, name }] })  // enumerable set
});
```

### ResourceContent

```ts
{ uri: string, mimeType?: string, text?: string, blob?: string }
```

## registerPrompt

```ts
server.registerPrompt(
    name: string,
    config: {
        title?: string;
        description?: string;
        argsSchema?: ZodObject;       // argument schema
    },
    callback: (args, extra) => ({
        messages: PromptMessage[];
    })
);
```

### PromptMessage

```ts
{
    role: 'user' | 'assistant',
    content: ContentBlock | ResourceContent  // text, image, audio, resource_link, resource
}
```

## Transports

### stdio

```ts
import { serveStdio } from '@modelcontextprotocol/server/stdio';

void serveStdio(createServer);  // factory function
```

### Streamable HTTP (stateless)

```ts
import { createMcpHandler } from '@modelcontextprotocol/server';

const handler = createMcpHandler((ctx) => {
    // ctx: { era, authInfo, requestInfo }
    const server = new McpServer({ name: 'my-server', version: '1.0.0' });
    // register tools/resources/prompts
    return server;
});

// handler.fetch  → (Request) => Promise<Response>  (web-standard)
// handler.close  → shutdown
// handler.notify → { toolsChanged(), resourcesChanged(), promptsChanged() }
// handler.bus    → ServerEventBus (for cross-node notifications)
```

### Sessionful (2025-era)

```ts
import { NodeStreamableHTTPServerTransport } from '@modelcontextprotocol/node';
import { randomUUID } from 'node:crypto';

const transport = new NodeStreamableHTTPServerTransport({
    sessionIdGenerator: () => randomUUID(),
    // eventStore: myEventStore,  // for stream resumability
    onsessioninitialized: (id) => { /* store transport in map */ }
});
```

### Framework mounting

```ts
// Express
import { createMcpExpressApp } from '@modelcontextprotocol/express';
const app = createMcpExpressApp(handler);  // Host/Origin validation armed by default

// Hono
import { createMcpHonoApp } from '@modelcontextprotocol/hono';
const app = createMcpHonoApp(handler);

// Fastify
import { createMcpFastifyApp } from '@modelcontextprotocol/fastify';
const app = createMcpFastifyApp(handler);

// Web-standard runtime (Workers, Deno, Bun)
export default handler;
```

## EventStore interface (stream resumability)

```ts
interface EventStore {
    storeEvent(streamId: string, message: JSONRPCMessage): Promise<string>;  // returns event id
    replayEventsAfter(lastEventId: string, opts: { send: (msg: JSONRPCMessage) => Promise<void> }): Promise<void>;
}
```

## ServerEventBus interface (cross-node scaling)

```ts
interface ServerEventBus {
    publish(event: ServerEvent): void;
    subscribe(listener: (event: ServerEvent) => void): () => void;  // returns unsubscribe
}

// Usage:
const handler = createMcpHandler(buildServer, { bus: redisBus });
```

## Testing with in-memory Client

```ts
import { Client } from '@modelcontextprotocol/client';

const client = new Client({ name: 'test', version: '1.0.0' });
// Connect to server in-memory (see v2 Testing guide for wiring)

// Call a tool
const result = await client.callTool({ name: 'search', arguments: { query: 'mug' } });

// Read a resource
const { contents } = await client.readResource({ uri: 'config://app' });

// Get a prompt
const { messages } = await client.getPrompt({ name: 'review-code', arguments: { code: 'let x = 1' } });
```

## v1 → v2 rename map

| v1 | v2 |
|---|---|
| `server.tool(name, ...)` | `server.registerTool(name, config, handler)` |
| `server.resource(name, ...)` | `server.registerResource(name, uri, config, cb)` |
| `server.prompt(name, ...)` | `server.registerPrompt(name, config, cb)` |
| `StreamableHTTPServerTransport` + `connect()` | `createMcpHandler(factory)` |
| Shared `McpServer` instance | Factory pattern (fresh per request) |
| `zod` (v3) | `zod/v4` (Standard Schema) |

## Key URLs

| Resource | URL |
|---|---|
| v2 docs home | `https://ts.sdk.modelcontextprotocol.io/v2/` |
| Build a server guide | `https://ts.sdk.modelcontextprotocol.io/v2/get-started/build-a-server` |
| Tools guide | `https://ts.sdk.modelcontextprotocol.io/v2/servers/tools` |
| Resources guide | `https://ts.sdk.modelcontextprotocol.io/v2/servers/resources` |
| Prompts guide | `https://ts.sdk.modelcontextprotocol.io/v2/servers/prompts` |
| HTTP serving guide | `https://ts.sdk.modelcontextprotocol.io/v2/serving/http` |
| Sessions/scaling guide | `https://ts.sdk.modelcontextprotocol.io/v2/serving/sessions-state-scaling` |
| GitHub repo | `https://github.com/modelcontextprotocol/typescript-sdk` |
| Examples directory | `https://github.com/modelcontextprotocol/typescript-sdk/tree/main/examples` |
| MCP spec (2026-07-28) | `https://modelcontextprotocol.io/specification/2026-07-28` |
| v1 legacy docs | `https://ts.sdk.modelcontextprotocol.io/` |
