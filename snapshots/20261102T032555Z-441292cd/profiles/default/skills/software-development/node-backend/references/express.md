# Express Reference

## When to Reach for Express

Use Express when you want a lightweight, explicit HTTP framework with minimal abstractions. It works well for small to medium APIs, custom middleware stacks, incremental legacy refactors, and teams that prefer direct control over routing and request flow.

## Baseline Structure

```text
src/
├── app.ts
├── server.ts
├── routes/
├── controllers/
├── services/
├── middlewares/
├── validators/
├── config/
└── utils/
```

## Core Patterns

### App/bootstrap split

Keep app construction separate from process startup so tests can import the app without binding a port.

```ts
// app.ts
export function buildApp() {
  const app = express();
  app.use(express.json());
  return app;
}

// server.ts
const app = buildApp();
app.listen(process.env.PORT ?? 3000);
```

### Route → controller → service flow

- Routes define URL shape and middleware
- Controllers translate HTTP to domain calls
- Services hold business logic
- Persistence stays behind services/repositories

### Error handling

Register error middleware last.

```ts
app.use((err, req, res, next) => {
  res.status(err.statusCode ?? 500).json({
    code: err.code ?? 'INTERNAL_ERROR',
    message: err.message ?? 'Something went wrong',
  });
});
```

### Async wrapper

```ts
const asyncHandler = (fn) => (req, res, next) =>
  Promise.resolve(fn(req, res, next)).catch(next);
```

## Middleware Guidance

Common middleware order:
1. request id / logging context
2. security headers (`helmet`)
3. CORS
4. body parsing
5. auth
6. rate limiting
7. routes
8. error handler

## Validation

Prefer schema validation at the edge with Zod, Joi, or Yup. Validate `body`, `params`, and `query` separately when possible.

```ts
const result = schema.safeParse(req.body);
if (!result.success) {
  return res.status(400).json({ errors: result.error.flatten() });
}
```

## Testing

Use `supertest` for route-level integration tests and plain unit tests for services. Keep port binding out of test imports.

## Common Pitfalls

1. Putting business logic directly in route handlers.
2. Calling `next(err)` inconsistently across async routes.
3. Returning stack traces in production responses.
4. Mutating `req.body` without clear typing.
5. Registering the error handler before routes.

## Checklist

- [ ] App creation is separate from `listen()`
- [ ] Async routes are wrapped consistently
- [ ] Validation happens before service calls
- [ ] Error middleware is registered last
- [ ] Tests import the app without opening a socket
