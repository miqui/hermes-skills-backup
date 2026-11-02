# Fastify Reference

## When to Reach for Fastify

Use Fastify when you want strong performance, schema-driven validation/serialization, low overhead, and a plugin-oriented architecture. It works well for high-throughput APIs, services that benefit from JSON schema contracts, and teams that want more structure than bare Express without the full NestJS abstraction layer.

## Baseline Structure

```text
src/
├── app.ts
├── server.ts
├── plugins/
├── routes/
├── controllers/
├── services/
├── schemas/
├── hooks/
├── config/
└── utils/
```

## Core Patterns

### Build function split

Keep app construction separate from process startup so tests can create an app instance without binding a port.

```ts
// app.ts
export async function buildApp() {
  const app = Fastify({ logger: true });
  return app;
}

// server.ts
const app = await buildApp();
await app.listen({ port: Number(process.env.PORT ?? 3000), host: '0.0.0.0' });
```

### Plugin-first composition

Register shared concerns as plugins and keep route registration shallow.

- plugins configure cross-cutting concerns
- routes define endpoints and schema
- services hold business logic
- persistence stays behind services/repositories

### Schema-driven handlers

Prefer route schemas for `params`, `querystring`, `body`, and `response` so validation and serialization stay aligned.

```ts
app.post('/users', {
  schema: {
    body: userBodySchema,
    response: {
      201: userResponseSchema,
    },
  },
}, async (request, reply) => {
  const user = await userService.create(request.body);
  return reply.code(201).send(user);
});
```

## Hooks and Plugins

Use hooks sparingly and keep them predictable.

Common order:
1. logging/request id
2. security plugins
3. auth decorators/hooks
4. shared plugins
5. routes
6. error handler / not-found handler

Prefer `decorate`, `decorateRequest`, and plugins for shared behavior over mutating request objects ad hoc.

## Validation and Serialization

Fastify works best when schemas are first-class. Reuse shared schemas and avoid duplicating TypeScript-only types that drift away from runtime validation.

## Testing

Use `app.inject()` for fast integration tests without opening a network port. Test plugins and route registration through the built app instance.

## Common Pitfalls

1. Treating Fastify exactly like Express and ignoring plugins/schemas.
2. Skipping response schemas and losing serialization guarantees.
3. Mixing runtime validation and TypeScript types with no shared source of truth.
4. Registering plugins in an order that breaks decorators or hooks.
5. Testing via real network ports instead of `inject()` when not needed.

## Checklist

- [ ] App creation is separate from `listen()`
- [ ] Route schemas validate input and shape responses
- [ ] Shared behavior lives in plugins/decorators
- [ ] Plugin registration order is intentional
- [ ] Tests use `app.inject()` where possible
