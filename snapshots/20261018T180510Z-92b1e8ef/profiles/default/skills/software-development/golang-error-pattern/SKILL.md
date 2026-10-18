---
name: golang-error-pattern
description: "Use when writing or reviewing Go error handling: stdlib wrapping with %w, errors.Is/As, sentinel and typed errors, panic-recovery boundaries, and (when richer context is needed) structured errors with samber/oops, machine-readable codes, and user-safe messages."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [golang, go, errors, errors-is-as, observability, logging, panic-recovery]
    related_skills: [golang-troubleshooting, golang-security, golang-testing]
---

# Go Error Handling: Stdlib Baseline and Structured Errors

## Overview

Start with the standard library: plain errors wrapped with `%w`, inspected with `errors.Is`/`errors.As`. That is enough for most code. Reach for a structured-error library only when you need attached attributes, stack traces, machine-readable codes, trace IDs, ownership hints, or explicit user-safe messages.

The structured examples use `samber/oops` (API checked against v1.x; module `github.com/samber/oops`, zero dependencies), but the guidance applies to any structured-error library or custom abstraction.

## Stdlib Baseline (use this first)

```go
var ErrNotFound = errors.New("user not found") // sentinel: callers compare with errors.Is

type ValidationError struct{ Field string }     // typed: callers extract with errors.As
func (e *ValidationError) Error() string { return "invalid " + e.Field }

func (r *Repo) GetUser(ctx context.Context, id string) (*User, error) {
    var u User
    err := r.db.QueryRowContext(ctx, "SELECT id, name FROM users WHERE id = $1", id).
        Scan(&u.ID, &u.Name)
    switch {
    case errors.Is(err, sql.ErrNoRows):
        return nil, fmt.Errorf("get user %q: %w", id, ErrNotFound)
    case err != nil:
        return nil, fmt.Errorf("get user %q: %w", id, err)
    }
    return &u, nil
}

// Caller
if errors.Is(err, ErrNotFound) { /* 404 */ }
var ve *ValidationError
if errors.As(err, &ve) { /* 400, use ve.Field */ }
```

Rules:

- Wrap with `%w` when callers may need to inspect the cause; use `%v` to deliberately hide it.
- Add context once per layer ("get user: ..."), not the same text repeatedly.
- Handle an error or return it — do not log and return (duplicate logs).
- `errors.As` takes a pointer to the target type (`&ve` where `ve` is `*ValidationError`); never type-assert or compare `err == X` on wrapped errors.
- `errors.Join` combines independent errors (e.g. cleanup failures).
- Never expose raw `err.Error()` to end users; map to a safe message at the boundary.

## When to Use

- Designing a project-wide error-handling pattern in Go
- Reviewing whether errors carry enough operational context
- Deciding where to wrap, annotate, classify, or recover from failures
- Separating user-facing messages from developer diagnostics
- Adding trace IDs, attributes, owners, or error codes (structured errors)
- Establishing rules for panic recovery at safe boundaries

Do not use this skill as the primary reference for general production debugging workflow after the error has already surfaced; use `golang-troubleshooting` for root-cause investigation.

## Why Structured Errors Help (beyond the baseline)

Plain wrapped errors are often enough for small programs, but larger systems frequently need more than a message string:

- **structured context** for queries, IDs, domains, tenants, and operations
- **stack traces** for diagnosis
- **error codes** for programmatic handling
- **public messages** that are safe to show to users
- **low-cardinality messages** that group properly in logging and APM systems

The main rule is simple: keep the human-readable error message stable, and attach variable data as structured attributes.

## Core Pattern: Builder-Style Errors

The examples below use `oops` and its fluent builder pattern:

```go
err := oops.
    In("user-service").
    Tags("database", "postgres").
    Code("network_failure").
    User("user-123", "email", "foo@bar.com").
    With("query", query).
    Errorf("failed to fetch user")
```

Useful terminal methods include:

- `.Errorf(format, args...)`
- `.Wrap(err)`
- `.Wrapf(err, format, args...)`
- `.Join(err1, err2, ...)`
- `.Recover(fn)` / `.Recoverf(fn, format, args...)`

## Builder Methods Reference

| Method | Use case |
| --- | --- |
| `.With("key", value)` | Attach structured attributes |
| `.WithContext(ctx, "key1", "key2")` | Copy selected context values into the error |
| `.In("domain")` | Identify the service, package, or feature area |
| `.Tags("auth", "sql")` | Add categorical labels |
| `.Code("machine_readable_code")` | Set a stable programmatic identifier |
| `.Public("Could not fetch user.")` | Set a user-safe message |
| `.Hint("runbook or next step")` | Add a debugging hint |
| `.Owner("team-or-channel")` | Identify responsibility |
| `.User(id, "k", "v")` | Attach user context |
| `.Tenant(id, "k", "v")` | Attach tenant or organization context |
| `.Trace(id)` | Attach trace or correlation ID |
| `.Span(id)` | Attach span ID |
| `.Time(t)` / `.Since(t)` / `.Duration(d)` | Attach time-based diagnostics |
| `.Request(req, includeBody)` | Capture request context |
| `.Response(res, includeBody)` | Capture response context |
| `oops.FromContext(ctx)` | Start from a builder already attached to a context |

## Common Scenarios

### Database / Repository Layer

```go
func (r *UserRepository) FetchUser(ctx context.Context, id string) (*User, error) {
    var u User
    err := r.db.QueryRowContext(ctx, "SELECT id, name, email FROM users WHERE id = $1", id).
        Scan(&u.ID, &u.Name, &u.Email)
    if err != nil {
        // oops.Wrapf returns nil for a nil error, but here err is known non-nil.
        return nil, oops.
            In("user-repository").
            Tags("database", "postgres").
            With("user_id", id).
            Wrapf(err, "failed to fetch user") // errors.Is(err, sql.ErrNoRows) still works
    }
    return &u, nil
}
```

### HTTP Handler Layer

```go
func (h *Handler) CreateUser(w http.ResponseWriter, r *http.Request) error {
    userID := getUserID(r)

    err := h.service.CreateUser(r.Context(), userID)
    if err != nil {
        return oops.
            In("http-handler").
            Tags("endpoint", "/users").
            Request(r, false).
            User(userID).
            Wrapf(err, "create user failed")
    }

    w.WriteHeader(http.StatusCreated)
    return nil
}
```

### Service Layer with Reusable Builder

```go
func (s *UserService) CreateOrder(ctx context.Context, req CreateOrderRequest) error {
    builder := oops.
        In("order-service").
        Tags("orders", "checkout").
        Tenant(req.TenantID, "plan", req.Plan).
        User(req.UserID, "email", req.UserEmail)

    product, err := s.catalog.GetProduct(ctx, req.ProductID)
    if err != nil {
        return builder.
            With("product_id", req.ProductID).
            Wrapf(err, "product lookup failed")
    }

    if product.Stock < req.Quantity {
        return builder.
            Code("insufficient_stock").
            Public("Not enough items in stock.").
            With("requested", req.Quantity).
            With("available", product.Stock).
            Errorf("insufficient stock")
    }

    return nil
}
```

## Wrapping Best Practices

### Wrap directly when the API handles nil safely

```go
return oops.Wrapf(err, "operation failed")
```

Prefer the direct form when the library returns `nil` for `nil` input. It reduces repetitive boilerplate.

### Add context at meaningful boundaries

Add error context where the layer has new information to contribute, especially across package or architectural boundaries:

```go
func Controller() error {
    return oops.In("controller").Trace(traceID).Wrapf(Service(), "user request failed")
}

func Service() error {
    return oops.In("service").With("op", "create_user").Wrapf(Repository(), "db operation failed")
}

func Repository() error {
    return oops.In("repository").Tags("database", "postgres").Errorf("connection timeout")
}
```

### Keep messages low-cardinality

Avoid interpolating request-specific or user-specific values into the main message when logs and APM tools need grouping:

```go
// Bad: high-cardinality message
oops.Errorf("failed to process user %s in tenant %s", userID, tenantID)

// Better: stable message + structured attributes
oops.With("user_id", userID).With("tenant_id", tenantID).Errorf("failed to process user")
```

## Panic Recovery

Recover panics only at boundaries where converting a panic into a structured error is appropriate, such as worker entry points, goroutine boundaries, or external request handlers.

```go
func ProcessData(data string) error {
    return oops.
        In("data-processor").
        Code("panic_recovered").
        Hint("Check input data format and dependencies").
        Recover(func() {
            riskyOperation(data)
        })
}
```

`Recover` returns an error (nil if no panic). It only catches panics in the calling goroutine — a goroutine started inside the callback needs its own `Recover`/`recover()`.

Do not scatter panic recovery deep inside normal business logic. That tends to hide defects rather than surface them cleanly.

## Accessing Error Information

```go
if oopsErr, ok := oops.AsOops(err); ok { // errors.As under the hood: finds it through wrapping
    fmt.Println("Code:", oopsErr.Code())
    fmt.Println("Domain:", oopsErr.Domain())
    fmt.Println("Tags:", oopsErr.Tags())
    fmt.Println("Context:", oopsErr.Context())
    fmt.Println("Stacktrace:", oopsErr.Stacktrace())
}

// Equivalent stdlib form:
var oopsErr oops.OopsError
if errors.As(err, &oopsErr) { /* ... */ }

publicMsg := oops.GetPublic(err, "Something went wrong")
```

Avoid the bare assertion `err.(oops.OopsError)`: it panics or fails when the error is wrapped by `fmt.Errorf`.

## Context Propagation

Carry request-level or trace-level metadata through `context.Context` when the error library supports it:

```go
func middleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        builder := oops.
            In("http").
            Request(r, false).
            Trace(r.Header.Get("X-Trace-ID"))

        ctx := oops.WithBuilder(r.Context(), builder)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

func handler(ctx context.Context) error {
    return oops.FromContext(ctx).Tags("handler", "users").Errorf("something failed")
}
```

For assertions, configuration, and logger integration details, see [Advanced patterns](./references/advanced.md).

## Common Pitfalls

1. Putting variable request data into the error message instead of structured fields
2. Wrapping the same failure repeatedly without adding meaningful new context
3. Mixing developer-only diagnostics with user-facing messages
4. Recovering panics too deep in the call stack and hiding programming bugs
5. Treating structured errors as a substitute for clear logs, metrics, and traces

## Usage Checks

- [ ] Plain `fmt.Errorf("...: %w", err)` is used unless attributes/codes/stack traces are actually needed
- [ ] Callers use `errors.Is`/`errors.As`, never string matching or `==` on wrapped errors
- [ ] Variable data lives in attributes (`With`), not in the message
- [ ] Public messages (`Public`) never leak internals; developer detail stays in logs
- [ ] `Recover` appears only at goroutine/request/worker boundaries
