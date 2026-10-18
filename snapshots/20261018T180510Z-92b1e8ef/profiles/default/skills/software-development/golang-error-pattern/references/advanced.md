# Advanced Patterns

## Assertions

Assertions panic when the condition is false. `oops.Assert`/`oops.Assertf` exist at package level and on builders (`oops.In("x").Assertf(...)` returns the builder so calls chain). Wrap them in `Recover` to turn the panic into an error. Use them for invariants (bugs), never for validating user input — return a normal error for that:

```go
func applyDiscount(price, pct int) error {
    return oops.
        In("pricing").
        Recover(func() {
            oops.Assertf(pct >= 0 && pct <= 100, "pct out of range: %d", pct) // programmer error
            oops.Assert(price >= 0)
            // ... logic
        })
}
```

Assertions should be rare in Go. Use them only for truly impossible states that indicate a bug.

## Configuration

Package-level variables (not goroutine-safe; set once at startup):

```go
oops.StackTraceMaxDepth = 20          // default 10
oops.SourceFragmentsHidden = false    // default true; reads source files at runtime
loc, err := time.LoadLocation("America/New_York")
if err == nil { oops.Local = loc }    // default time.UTC
// Also: oops.AutoTraceID (default true: ULID trace IDs), oops.DereferencePointers (default true)
```

## Logger integration

```go
if oopsErr, ok := oops.AsOops(err); ok {
    userID, _ := oopsErr.User() // User() returns (id, attributes)
    slog.Error("operation failed",
        "code", oopsErr.Code(),
        "domain", oopsErr.Domain(),
        "user_id", userID,
        "error", err,
    )
}

// With slog (oops errors implement slog.LogValuer): keep the message stable
slog.Error("operation failed", slog.Any("error", err))

// With zerolog / logrus: use the formatters in github.com/samber/oops/loggers/*
log.Error().Err(err).Msg("operation failed")
log.WithError(err).Error("operation failed")
```
