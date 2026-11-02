# Code Style Details

## Extract Complex Conditions

When `if` conditions span multiple meaningful operands, extract the underlying business concepts into named booleans:

```go
// Good — self-documenting
isAdmin := user.Role == RoleAdmin
isOwner := resource.OwnerID == user.ID
hasOverride := permissions.Contains(PermOverride)
if isAdmin || isOwner || hasOverride {
    allow()
}

// Bad — wall of logic
if user.Role == RoleAdmin || resource.OwnerID == user.ID || permissions.Contains(PermOverride) {
    allow()
}
```

**Exception:** When the last condition involves expensive processing, keep it inline so short-circuit evaluation can skip the expensive work:

```go
// Good — avoid expensive operation when possible
if isAdmin || isOwner || expensivePermissionCheck(user, resource) {
    allow()
}

// Wasteful — always runs expensive check
canOverride := expensivePermissionCheck(user, resource)
if isAdmin || isOwner || canOverride {
    allow()
}
```

## Value vs Pointer Arguments

This section covers **function parameters**, not method receivers.

Pass small, fixed-size types by value — strings are already a small descriptor internally:

```go
// Good — value types by value
func FormatUser(name string, age int, createdAt time.Time) string

// Good — pointer for mutation
func PopulateDefaults(cfg *Config)

// Good — pointer when nil is meaningful (optional field update)
func UpdateUser(ctx context.Context, id string, name *string) error

// Bad — pointer for no reason
func Greet(name *string) string
```

**When to use pointers**:

- The function mutates the value
- The struct is large enough that copying is meaningful
- Nil is meaningful for optional or nullable input

**When not to use pointers**:

- `string`, `int`, `bool`, `float64`, `time.Time` — usually pass by value
- Read-only access to small structs — often clearer and faster by value
- "Just to save memory" when the copy cost is negligible

**Performance trade-offs when they matter**:

- **Values:** better locality, no extra indirection, usually simpler for small types
- **Pointers:** useful for mutation, nil semantics, and larger structs where copies are more expensive
- **Rule of thumb:** for small read-only values, prefer values; for mutation or larger structs, pointers are often the right fit. Benchmark when uncertain.
