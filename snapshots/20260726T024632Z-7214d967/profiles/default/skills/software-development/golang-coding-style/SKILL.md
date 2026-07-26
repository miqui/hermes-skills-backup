---
name: golang-coding-style
description: "Use when writing or reviewing Go code for readability, control flow clarity, function shape, code organization, and style decisions that require judgment beyond what gofmt and linters enforce."
version: 1.0.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [golang, go, style, readability, conventions, code-review]
    related_skills: [go-builder, golang-lint, golang-concurrency, golang-testing]
---

# Go Coding Style

## Overview

This skill covers Go style decisions that require human judgment after `gofmt`, `goimports`, and linters have done their work. It focuses on readability, maintainability, and clear intent in code structure.

Use this skill for choices like line breaking, control-flow shape, function boundaries, variable declarations, code organization, and when to prefer simple explicit code over clever abstractions.

## When to Use

- Writing new Go code and you want consistent style guidance
- Reviewing Go code for readability and maintainability
- Deciding between multiple clear-but-different code shapes
- Establishing team conventions that are broader than formatter output

Do not use this skill as the primary reference for concurrency patterns, security guidance, or test strategy when a more specific Go skill matches better.

> "Clear is better than clever." — Go Proverbs

When ignoring a rule, add a short comment to explain why.

## Line Length & Breaking

No rigid line limit, but lines beyond ~120 characters SHOULD usually be broken. Break at **semantic boundaries**, not arbitrary column counts. Function calls with 4+ arguments SHOULD usually use one argument per line:

```go
// Good — each argument on its own line, closing paren separate
mux.HandleFunc("/api/users", func(w http.ResponseWriter, r *http.Request) {
    handleUsers(
        w,
        r,
        serviceName,
        cfg,
        logger,
        authMiddleware,
    )
})
```

When a function signature is too long, the real fix is often **fewer parameters** by grouping related inputs into a struct rather than relying only on wrapping.

## Variable Declarations

Use `:=` for non-zero values and `var` for explicit zero-value initialization. The form should signal intent:

```go
var count int              // zero value, set later
name := "default"          // non-zero, := is appropriate
var buf bytes.Buffer       // zero value is ready to use
```

### Slice & Map Initialization

Slices and maps SHOULD be initialized deliberately rather than left nil unless nil carries semantic meaning. Nil maps panic on write, and nil slices serialize to `null` in JSON rather than `[]`, which can surprise API consumers.

```go
users := []User{}                       // initialized empty slice
m := map[string]int{}                   // initialized empty map
users := make([]User, 0, len(ids))      // preallocate when capacity is known
m := make(map[string]int, len(items))   // preallocate when size is known
```

Do not preallocate speculatively — `make([]T, 0, 1000)` wastes memory when the common case is much smaller.

### Composite Literals

Composite literals SHOULD use field names. Positional fields become fragile when a type grows or reorders fields:

```go
srv := &http.Server{
    Addr:         ":8080",
    ReadTimeout:  5 * time.Second,
    WriteTimeout: 10 * time.Second,
}
```

## Control Flow

### Reduce Nesting

Handle errors and edge cases early. Keep the happy path at minimal indentation:

```go
func process(data []byte) (*Result, error) {
    if len(data) == 0 {
        return nil, errors.New("empty data")
    }

    parsed, err := parse(data)
    if err != nil {
        return nil, fmt.Errorf("parsing: %w", err)
    }

    return transform(parsed), nil
}
```

### Eliminate Unnecessary `else`

When the `if` body ends with `return`, `break`, or `continue`, drop the `else`. For simple assignments, prefer default-then-override or `switch` when that makes the default obvious:

```go
// Good — default-then-override with switch
level := slog.LevelInfo
switch {
case debug:
    level = slog.LevelDebug
case verbose:
    level = slog.LevelWarn
}

// Bad — else-if chain hides that there's a default
if debug {
    level = slog.LevelDebug
} else if verbose {
    level = slog.LevelWarn
} else {
    level = slog.LevelInfo
}
```

### Complex Conditions & Init Scope

When an `if` condition has 3+ meaningful operands, extract the important business concepts into named booleans. That reduces visual noise and makes the policy obvious. See [details](./references/details.md).

```go
// Good — named booleans make intent clear
isAdmin := user.Role == RoleAdmin
isOwner := resource.OwnerID == user.ID
isPublicVerified := resource.IsPublic && user.IsVerified
if isAdmin || isOwner || isPublicVerified || permissions.Contains(PermOverride) {
    allow()
}
```

Scope variables to `if` blocks when they are only needed for the check:

```go
if err := validate(input); err != nil {
    return err
}
```

### Switch Over If-Else Chains

When comparing the same variable multiple times, prefer `switch`:

```go
switch status {
case StatusActive:
    activate()
case StatusInactive:
    deactivate()
default:
    panic(fmt.Sprintf("unexpected status: %d", status))
}
```

## Function Design

- Functions SHOULD be short and focused
- Prefer one function, one job
- Functions with more than 4 parameters deserve scrutiny; often a struct or redesign is clearer
- Put `context.Context` first when present
- Prefer explicit returns in longer functions over naked returns

```go
func FetchUser(ctx context.Context, id string) (*User, error)
func SendEmail(ctx context.Context, msg EmailMessage) error
```

### Prefer `range` for Iteration

Use `range` over index-based loops unless indexes are themselves the important value. Use `range n` on Go 1.22+ for simple counting when appropriate.

```go
for _, user := range users {
    process(user)
}
```

## Value vs Pointer Arguments

Pass small types (`string`, `int`, `bool`, `time.Time`) by value. Use pointers when mutating, for larger structs, or when nil is meaningful. See [details](./references/details.md).

## Code Organization Within Files

- Group related declarations: type, constructor, methods together
- Order files predictably: package docs, imports, constants, types, constructors, methods, helpers
- Prefer one primary type per file when that type has significant behavior
- Restrict blank imports to places where side effects are obvious
- Avoid dot imports in normal code
- Keep symbols unexported until there is a real need to expose them

## String Handling

Use `strconv` for simple conversions and `fmt.Sprintf` for richer formatting. Use `%q` in error messages when visible string boundaries help debugging. Use `strings.Builder` in loops; use `+` for simple concatenation.

## Type Conversions

Prefer explicit, narrow conversions. Use generics over `any` when a concrete type will do:

```go
func Contains[T comparable](slice []T, target T) bool
```

## Philosophy

- **A little copying is better than a little dependency**
- Use standard-library helpers first; add third-party helpers only when they clearly improve clarity
- Avoid reflection unless it is genuinely necessary
- Do not abstract prematurely
- Minimize public surface area; exported names are commitments

## Reviewing a Large Codebase

When reviewing code style across a large codebase, split the review by concern: control flow, function design, declarations, string handling, and code organization. Parallel review is helpful when your current agent setup supports it, but the review output should still be consolidated into one coherent set of recommendations.

## Enforce with Linters

Many style-adjacent rules are enforced automatically by `gofmt`, `goimports`, `gofumpt`, `gocritic`, `revive`, and related linters. Use `golang-lint` for automated enforcement guidance.

## Common Pitfalls

1. Treating formatter output as a complete style guide. Formatters remove noise, but they do not make architecture or control flow clear.
2. Using pointers by default. Prefer values unless mutation, size, or nil semantics justify pointers.
3. Keeping deeply nested code when early returns would flatten the happy path.
4. Adding abstraction before a pattern is stable.
5. Exporting names too early and expanding the package surface without a clear need.

## Verification Checklist

- [ ] The skill name matches the directory: `golang-coding-style`
- [ ] The description starts with `Use when ...`
- [ ] Cross-references point only to real local skills or plain guidance
- [ ] The body focuses on human judgment, not formatter behavior alone
