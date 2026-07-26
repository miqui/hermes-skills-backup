---
name: graphql-api
description: "Use when designing, implementing, reviewing, testing, securing, or optimizing GraphQL APIs and schemas across languages and runtimes. Covers schema-first contract design, resolver boundaries, queries and mutations, pagination, nullability, errors, authorization, batching/DataLoader patterns, query cost controls, observability, federation boundaries, and safe evolution of GraphQL contracts."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [graphql, gql, api, schema, resolvers, dataloader, federation, query-cost, pagination]
    related_skills: [api-governance, node-backend, code-performance-engineering, test-driven-development, requesting-code-review, application-authorization]
---

# GraphQL API

## Overview

Use this skill for GraphQL API work where the primary artifact is a GraphQL schema plus the resolver/runtime behavior behind it. Treat the schema as a public contract: fields, types, arguments, nullability, pagination, directives, mutations, subscriptions, deprecations, and error behavior all shape the consumer experience.

GraphQL is not just REST with a different syntax. It changes where complexity lives: clients can select fields and traverse relationships, while the server must enforce authorization, cost limits, resolver batching, data-access boundaries, and observability. A good GraphQL API gives clients flexibility without exposing database internals, allowing arbitrary expensive queries, or hiding errors behind inconsistent `null` values.

For API lifecycle and governance gates, pair with `api-governance`. For Node.js implementation details, pair with `node-backend`. For resolver fan-out, N+1, batching, latency, or query complexity performance work, pair with `code-performance-engineering`. For pre-commit verification or PR review, pair with `requesting-code-review`. For authorization model design — RBAC/ABAC/ReBAC structure, role and permission lifecycle, policy enforcement point architecture — pair with `application-authorization`; this skill covers GraphQL-specific enforcement (resolver/field-level policy placement, context wiring, tenant scoping) but delegates the underlying authorization model to that skill.

## When to Use

Use this skill when the task involves:

- Designing or reviewing a GraphQL schema.
- Adding GraphQL queries, mutations, subscriptions, types, inputs, enums, interfaces, or unions.
- Deciding field names, nullability, pagination, filtering, sorting, or connection shapes.
- Implementing or reviewing resolvers and resolver boundaries.
- Preventing N+1 queries with batching/loaders.
- Adding authorization, authentication context, tenant scoping, or field-level policy checks.
- Setting query depth, query cost, timeout, persisted query, or rate-limit controls.
- Testing GraphQL operations with realistic documents, variables, auth contexts, and error cases.
- Evolving a GraphQL contract with deprecations and backward-compatible changes.
- Reviewing federation/subgraph boundaries or entity ownership.

Do not use this skill as the only guide when:

- The task is purely REST/OpenAPI contract design; use `openapi-api-designer` or `openapi-specification` instead.
- The task is generic backend architecture with no GraphQL-specific schema/resolver concerns; use the runtime-specific backend skill.
- The task is only performance methodology; use `code-performance-engineering` and pair this skill for GraphQL-specific bottlenecks.
- The task is only API lifecycle governance; use `api-governance` first and pair this skill at the contract/design stage.

## GraphQL Design Principles

1. **Schema is the contract**
   Design the schema intentionally and review it like a public API. Avoid leaking table names, ORM relationships, internal IDs, or accidental implementation details.

2. **Resolvers are orchestration boundaries**
   Resolvers should translate GraphQL operations into service/domain calls. Keep business logic in services, policies, and domain layers rather than embedding it inside field resolvers.

3. **Nullability is product semantics**
   Use non-null only when the value is always available and failure should propagate. Use nullable fields when absence is valid or authorization/error behavior requires partial results.

4. **Every relationship has a cost**
   Nested selection is powerful but can create N+1 queries, large result sets, recursive fan-out, and expensive joins. Design cost controls early.

5. **Authorization must be consistent**
   Auth checks must not depend on which resolver path a client uses. Put policy checks at stable domain/service boundaries and keep context typed and request-scoped.

6. **Evolution beats version proliferation**
   GraphQL schemas usually evolve via additive changes and deprecations rather than URL versions. Plan compatibility and removal windows explicitly.

## Schema Design Checklist

### Types and fields

- Prefer clear domain names over database or ORM names.
- Model stable product concepts, not transient UI implementation details.
- Use explicit object types instead of unstructured JSON blobs unless the value is truly schemaless.
- Keep field names consumer-oriented and consistent.
- Avoid fields whose meaning changes based on hidden server context.
- Document non-obvious fields and arguments.

### Nullability

- Default to nullable while designing, then make fields non-null only when the guarantee is strong.
- Avoid non-null chains that can null out large parts of a response when one leaf fails.
- Use non-null for required mutation inputs and values that are guaranteed by the domain.
- Be explicit about whether missing data means not found, unauthorized, not computed, or temporarily unavailable.

### Inputs and mutations

- Use input object types for mutations rather than long argument lists.
- Name mutation inputs and payloads consistently, for example `CreateUserInput` and `CreateUserPayload`.
- Return enough payload data for clients to update local state without immediate refetching.
- Keep mutations action-oriented but domain-aligned: `createInvoice`, `archiveProject`, `assignIssue`.
- Use idempotency keys where retries can create duplicate side effects.

### Enums, interfaces, and unions

- Use enums for stable finite values with documented meaning.
- Use interfaces when multiple types share fields and consumers can rely on the common shape.
- Use unions when the result can be one of several distinct object types without shared fields.
- Include `__typename` in client examples for polymorphic results.

### Pagination, filtering, and sorting

- Use cursor-based pagination for large or mutable collections.
- Prefer connection-style pagination when clients need edges, cursors, and pageInfo.
- Define stable sort order; cursor pagination without stable ordering is fragile.
- Bound `first` / `last` values with server-side maximums.
- Keep filters explicit and indexed where possible; avoid exposing arbitrary database predicates.

Example connection shape:

```graphql
type ProjectConnection {
  edges: [ProjectEdge!]!
  pageInfo: PageInfo!
  totalCount: Int
}

type ProjectEdge {
  node: Project!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

## Resolver Architecture

Keep resolvers thin:

```text
GraphQL resolver
  -> parse args and context
  -> call service/domain method
  -> return DTO/object for schema

Service/domain layer
  -> authorization and business rules
  -> data access orchestration
  -> transactions and side effects

Repository/data layer
  -> database or external API access
  -> query shape and persistence details
```

Resolver rules:

- Do not put business workflows directly in resolvers.
- Do not call databases repeatedly from nested field resolvers without batching.
- Do not assume parent resolvers already enforced all required authorization.
- Do not return raw ORM records if they contain internal or sensitive fields.
- Do not make resolvers depend on global mutable state.
- Keep request-scoped context explicit: identity, tenant, permissions, loaders, request id, logger, and services.

## Batching and N+1 Control

GraphQL makes N+1 mistakes easy because nested fields can trigger repeated loads. Use request-scoped loaders or equivalent batching patterns for repeated entity access.

Good loader properties:

- Created per request, not process-global, so auth/tenant context is correct.
- Batches equivalent lookups into one database/API call.
- Preserves result order and returns `null` or typed errors consistently for missing entities.
- Uses cache keys that include tenant/scope when necessary.
- Has bounded lifetime and does not become a cross-user cache.

Example pattern:

```ts
const userLoader = new DataLoader(async (ids: readonly string[]) => {
  const users = await userService.findManyByIds(ids as string[]);
  const byId = new Map(users.map((user) => [user.id, user]));
  return ids.map((id) => byId.get(id) ?? null);
});
```

Pair with `code-performance-engineering` when N+1, resolver fan-out, nested query cost, database time, or p95/p99 latency is the main issue.

## Authorization and Context

A robust GraphQL context usually includes:

- Authenticated subject or anonymous marker.
- Tenant/account/org scope.
- Permission or role information.
- Request-scoped loaders.
- Request id / trace id.
- Logger and metrics handles.
- Service clients configured for the request.

> **Scope boundary with `application-authorization`:** This skill covers *where* enforcement happens in a GraphQL stack — resolver/field-level placement, context wiring, tenant scoping, ensuring loaders don't leak data across authorization boundaries, and expressing outcomes cleanly as errors or null. The *design* of the authorization model itself — which roles/permissions/attributes exist, how they are administered, and where policy enforcement points live in the broader system — belongs to `application-authorization`. Load that skill when the authorization model or lifecycle is in scope.

Authorization checklist:

- Authenticate once at the boundary, before resolver execution where possible.
- Enforce object-level and field-level authorization consistently.
- Keep policy checks in services or policy helpers so alternate resolver paths cannot bypass them.
- Avoid relying on client-hidden fields for security decisions.
- Ensure loaders do not cache data across users, tenants, or authorization scopes.
- Test unauthorized access for direct object queries and nested access paths.

## Error Modeling

GraphQL supports partial success, but error semantics must be intentional.

Use GraphQL errors for:

- Invalid operation shape or validation failures.
- Authentication failures.
- Authorization failures.
- Unexpected server failures.

Consider typed payload errors for expected business outcomes:

```graphql
type CreateProjectPayload {
  project: Project
  userErrors: [UserError!]!
}

type UserError {
  field: [String!]
  message: String!
  code: String!
}
```

Error rules:

- Do not leak stack traces, SQL, tokens, internal IDs, or policy internals.
- Use stable error codes for client handling.
- Decide whether authorization failures should be explicit errors or appear as missing data.
- Log full diagnostic details server-side with request correlation.
- Test partial-result behavior when child resolvers fail.

## Query Cost and Safety Controls

GraphQL APIs need guardrails because clients can shape queries.

Common controls:

- Maximum query depth.
- Query complexity or cost scoring.
- Maximum page size and result limits.
- Timeouts and cancellation.
- Rate limits per actor/token/IP/client.
- Persisted or allowlisted operations for public/high-risk APIs.
- Disable or restrict introspection in sensitive production contexts when appropriate.
- Disable overly expensive resolver paths or require narrower filters.
- Limit aliases, fragments, and recursive shapes if they amplify work.

Cost review questions:

- What is the worst-case query shape a client can send?
- Which fields trigger database, network, or expensive computation?
- Are list fields bounded at every level?
- Can aliases duplicate expensive work?
- Do fragments hide repeated expensive selections?
- Are timeout and cancellation propagated into downstream calls?

## Performance Review

GraphQL performance issues often appear as:

- N+1 database queries.
- Excessive nested fan-out.
- Unbounded list fields.
- Over-fetching in resolvers even when clients ask for few fields.
- Repeated authorization checks that hit storage.
- Loader cache missing due to inconsistent keys.
- Slow computed fields inside large lists.
- Missing database indexes for common filters/sorts.
- Large response serialization overhead.

Use `code-performance-engineering` when performance work needs baselines, profiling/tracing, Big-O/fan-out analysis, benchmark design, or regression guardrails. For GraphQL specifically, capture:

- Operation name and variables.
- Query depth and complexity score.
- Resolver timings.
- Loader batch sizes and cache hit rates.
- Database query count and total DB time.
- Response size and serialization time.
- p50/p95/p99 latency by operation.

## Schema Evolution

Prefer additive evolution:

- Add new fields/types/arguments without breaking existing clients.
- Deprecate fields with clear reasons and replacements.
- Avoid changing field meanings, enum meanings, or nullability in breaking ways.
- Do not remove deprecated fields until usage shows clients have migrated.
- Track field usage if the platform supports it.

Breaking changes include:

- Removing fields, types, enum values, arguments, or mutations.
- Renaming fields or changing return types.
- Making nullable output fields non-null without absolute guarantee.
- Making optional arguments required.
- Changing pagination or ordering semantics unexpectedly.
- Changing error codes or authorization visibility behavior without notice.

Deprecation example:

```graphql
type User {
  fullName: String @deprecated(reason: "Use displayName instead.")
  displayName: String!
}
```

## Federation and Subgraphs

Use federation when independent teams or domains need to compose a graph while owning separate subgraphs. Do not use federation to avoid schema design decisions or to expose every service boundary directly to clients.

Federation checklist:

- Entity ownership is clear.
- Keys are stable and not implementation-only.
- Cross-subgraph references do not create excessive fan-out.
- Subgraph boundaries align with domain/team ownership.
- Composition checks run in CI.
- Breaking changes are detected before publishing.
- Auth and tenant context propagate consistently across subgraphs.

## Testing Strategy

Test at the operation boundary, not just resolver functions.

Include tests for:

- Valid queries and mutations with realistic variables.
- Invalid variables and schema validation failures.
- Authenticated, unauthenticated, unauthorized, and cross-tenant access.
- Nullability and partial-error behavior.
- Pagination boundaries and cursor stability.
- N+1-sensitive relation paths with query-count or loader assertions where feasible.
- Deprecation/migration paths when evolving schema.
- Query depth/cost rejection behavior.

Example operation test shape:

```graphql
query Project($id: ID!) {
  project(id: $id) {
    id
    name
    owner {
      id
      displayName
    }
  }
}
```

Use realistic GraphQL documents and variables in tests so validation, parsing, context, authorization, resolver wiring, and serialization are exercised together.

## Review Checklist

When reviewing a GraphQL change, check:

- [ ] Schema names and descriptions are consumer-oriented.
- [ ] Nullability choices are intentional and documented where surprising.
- [ ] Mutations use input objects and predictable payloads.
- [ ] List fields are paginated or otherwise bounded.
- [ ] Resolvers are thin and delegate business logic to services/domain code.
- [ ] Authorization cannot be bypassed through alternate resolver paths.
- [ ] N+1-sensitive paths use request-scoped batching/loaders.
- [ ] Query depth, cost, timeout, and result-size controls are appropriate for exposure level.
- [ ] Errors do not leak sensitive implementation details.
- [ ] Tests use real operations, variables, and auth contexts.
- [ ] Backward compatibility and deprecation behavior are considered.
- [ ] Observability captures operation-level and resolver-level signals where needed.

## Common Pitfalls

1. **Treating GraphQL as a database mirror.** Exposing tables and relationships directly creates a brittle public contract and leaks internals.

2. **Putting business logic in resolvers.** Resolvers should orchestrate, not own domain behavior.

3. **Ignoring N+1 until production.** Add batching/loaders and query-count awareness before relation-heavy fields become hot paths.

4. **Using non-null too aggressively.** Non-null errors can null out parent objects and surprise clients.

5. **Leaving list fields unbounded.** Flexible selection plus unbounded lists creates dangerous worst-case queries.

6. **Relying on UI behavior for security.** Clients can send arbitrary valid operations unless the server enforces policy.

7. **Using nullable fields as silent error handling.** Clients need distinguishable semantics for absent, unauthorized, failed, and unknown values.

8. **Skipping operation-level tests.** Unit-tested resolvers can still fail when schema validation, context, auth, loaders, and serialization interact.

9. **Breaking clients by changing field semantics.** Add and deprecate instead of mutating meaning in place.

10. **Creating global DataLoader instances.** Loaders should usually be request-scoped to avoid cross-user data leaks and stale auth context.

11. **Forgetting observability.** Without operation names, resolver timings, query counts, and trace context, GraphQL performance is hard to diagnose.

## Verification Checklist

Before calling GraphQL API work complete:

- [ ] The schema change is intentional, named clearly, and documented where needed.
- [ ] Nullability, pagination, and error behavior are explicit.
- [ ] Resolvers delegate to services/domain logic.
- [ ] Authorization is enforced consistently for direct and nested access paths.
- [ ] N+1-sensitive fields use batching/loaders or have a justified alternative.
- [ ] Query depth/cost/result-size controls match the API exposure risk.
- [ ] Tests cover realistic operations, variables, auth contexts, and failure paths.
- [ ] Backward compatibility and deprecations are handled for existing clients.
- [ ] Performance-sensitive changes include evidence or are paired with `code-performance-engineering`.
- [ ] Review or governance handoff uses `api-governance` when lifecycle decisions matter.
