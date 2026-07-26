---
name: golang-error-pattern
description: "Use when writing or reviewing Go error handling that needs structured context, wrapping discipline, machine-readable codes, panic recovery boundaries, and separation between developer diagnostics and user-facing messages."
version: 1.0.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [golang, go, errors, observability, logging, panic-recovery]
    related_skills: [golang-troubleshooting, golang-security, golang-testing]
---

# Structured Error Handling in Go

## Overview

This skill focuses on structured error handling patterns in Go, especially when the codebase uses richer error objects rather than plain wrapped strings. It is particularly relevant for workflows that need machine-readable codes, attached attributes, stack traces, tracing identifiers, ownership hints, or explicit user-safe messages.

The concrete examples here use `samber/oops`, but the broader guidance applies even when the implementation uses a different structured-error library or a custom internal abstraction.

## When to Use

- Designing a project-wide error-handling pattern in Go
- Reviewing whether errors carry enough operational context
- Deciding where to wrap, annotate, classify, or recover from failures
- Separating user-facing messages from developer diagnostics
- Adding trace IDs, attributes, owners, or error codes to improve debugging and observability
- Establishing rules for panic recovery at safe boundaries

Do not use this skill as the primary reference for general production debugging workflow after the error has already surfaced; use `golang-troubleshooting` for root-cause investigation.

## Why Structured Errors Help

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
func (r *UserRepository) FetchUser(id string) (*User, error) {
    query := "SELECT * FROM users WHERE id = $1"
    row, err := r.db.Query(query, id)
    if err != nil {
        return nil, oops.
            In("user-repository").
            Tags("database", "postgres").
            With("query", query).
            With("user_id", id).
            Wrapf(err, "failed to fetch user from database")
    }
    _ = row
    return nil, nil
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
func ProcessData(data string) (err error) {
    return oops.
        In("data-processor").
        Code("panic_recovered").
        Hint("Check input data format and dependencies").
        Recover(func() {
            riskyOperation(data)
        })
}
```

Do not scatter panic recovery deep inside normal business logic. That tends to hide defects rather than surface them cleanly.

## Accessing Error Information

```go
if oopsErr, ok := err.(oops.OopsError); ok {
    fmt.Println("Code:", oopsErr.Code())
    fmt.Println("Domain:", oopsErr.Domain())
    fmt.Println("Tags:", oopsErr.Tags())
    fmt.Println("Context:", oopsErr.Context())
    fmt.Println("Stacktrace:", oopsErr.Stacktrace())
}

publicMsg := oops.GetPublic(err, "Something went wrong")
```

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

## Verification Checklist

- [ ] The description starts with `Use when ...`
- [ ] The skill explains why structured attributes matter for grouping and diagnosis
- [ ] The guidance distinguishes public messages from developer diagnostics
- [ ] Panic recovery is framed as a boundary concern, not a blanket rule
- [ ] The advanced reference file still aligns with the main skill guidance
