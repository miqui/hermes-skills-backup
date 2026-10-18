# GraphQL Reference

## When to Reach for GraphQL

Use GraphQL when clients need flexible field selection, multiple related resources in one round trip, and an explicit typed schema that evolves over time. It works well for frontend-heavy products, internal platforms, and APIs where client data needs vary significantly across screens or consumers.

## Core Patterns

### Schema-first contract

Treat the GraphQL schema as a public contract. Keep naming, nullability, pagination, and deprecation decisions intentional.

### Resolver boundaries

- resolvers translate GraphQL operations into domain/service calls
- services hold business logic
- repositories/data access stay behind services or loaders
- auth and policy checks should happen consistently, not ad hoc per field

### Avoid N+1 queries

Use batching/loaders for nested relations instead of issuing one query per field resolution.

```ts
const userLoader = new DataLoader(async (ids: readonly string[]) => {
  const users = await userService.findManyByIds(ids as string[]);
  return ids.map((id) => users.find((u) => u.id === id) ?? null);
});
```

## Schema Design Guidance

Prefer:
- explicit object types over opaque JSON blobs
- cursor-based pagination for large lists
- input types for mutations
- clear error semantics at the API boundary

Be careful with:
- exposing internal database shape directly
- deeply nested graphs with uncontrolled cost
- nullable fields used as silent error handling

## Auth and Context

Build a typed request context that includes identity, permissions, loaders, and request-scoped services. Keep authorization checks close to domain actions.

## Performance and Safety

Use depth/complexity limits, persisted queries where needed, and observability around resolver latency. Expensive GraphQL queries should be measurable and controllable.

## Testing

Test schema-level behavior with realistic operations, variables, and auth contexts. Validate both successful queries and authorization/validation failures.

## Common Pitfalls

1. Putting business logic directly in resolvers.
2. Ignoring N+1 issues until production.
3. Exposing internal-only fields because they were easy to map.
4. Treating nullability inconsistently across the schema.
5. Skipping query complexity controls on public APIs.

## Checklist

- [ ] Schema acts as the public contract
- [ ] Resolvers delegate to services instead of embedding business logic
- [ ] N+1-sensitive paths use loaders/batching
- [ ] Query complexity and depth are controlled where needed
- [ ] GraphQL operations are tested with real variables and auth contexts
