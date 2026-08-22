# Node Backend Testing Reference

## Testing Strategy

Use a layered test strategy:

- unit tests for pure business logic and edge cases
- integration tests for database/repository behavior
- HTTP-level tests for request validation, auth, and response shape
- a small number of end-to-end tests for critical flows

Keep most tests fast and deterministic. Push framework bootstrapping and external I/O to the smaller integration/E2E layer.

## Core Patterns

### App/bootstrap split

Always separate app construction from server startup so tests can import the app without binding a port.

### Test factories

Use builders/factories for users, payloads, and entities so tests stay readable and only override what matters.

```ts
const makeUserInput = (overrides = {}) => ({
  email: 'user@example.com',
  name: 'Test User',
  password: 'StrongPass1',
  ...overrides,
});
```

### Arrange-Act-Assert

Keep each test focused on one behavior and one assertion cluster.

### Isolate side effects

Mock network calls, queues, email, and third-party APIs unless the test explicitly exercises those boundaries.

## Framework Guidance

### Express

Use `supertest(app)` for route-level tests and keep `listen()` out of imports.

### NestJS

Use `@nestjs/testing` to create a testing module. Override providers at the module boundary when possible.

### Fastify

Use `app.inject()` for route/integration tests and call `app.close()` in teardown.

## Database Testing

Prefer one of these patterns:

1. transaction rollback per test
2. truncate/reset between tests
3. ephemeral test database/container per suite

Do not let tests depend on execution order or shared leftover rows.

## Auth and Validation Coverage

Every protected endpoint should have tests for:
- unauthenticated access
- authenticated but unauthorized access
- malformed input
- valid success path

## What to Assert

Assert on stable contracts:
- status codes
- response body shape
- key side effects
- emitted domain events or calls to collaborators

Avoid brittle assertions on timestamps, full snapshots, or internal implementation details unless they are the contract.

## Common Pitfalls

1. Testing only the happy path.
2. Hitting real external services in routine test runs.
3. Sharing mutable fixtures across tests.
4. Over-mocking until tests no longer reflect real behavior.
5. Asserting large opaque snapshots instead of intentional fields.

## Checklist

- [ ] Tests are split across unit, integration, and HTTP/E2E where appropriate
- [ ] App creation is importable without opening a socket
- [ ] External side effects are mocked or isolated intentionally
- [ ] Protected endpoints cover auth failure and validation failure cases
- [ ] Test data setup is deterministic and cleaned up
