---
name: golang-testing
description: "Use when writing, reviewing, or improving Go tests, including unit tests, integration tests, table-driven tests, fuzzing, concurrency-sensitive tests, benchmark scaffolding, and test-suite design."
version: 1.0.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [golang, go, testing, unit-tests, integration-tests, fuzzing, benchmarks]
    related_skills: [golang-stretchr-testify, golang-lint, golang-troubleshooting, test-driven-development]
---

# Go Testing

## Overview

This skill covers production-quality testing practices for Go codebases. It focuses on writing tests that are fast, deterministic, behavior-oriented, and easy to maintain as the code evolves.

The goal is not to maximize coverage in the abstract. The goal is to make behavior explicit, prevent regressions, and keep failures easy to interpret.

## When to Use

- Writing new tests for Go code
- Reviewing or refactoring an existing Go test suite
- Deciding between unit, integration, fuzz, benchmark, or example tests
- Improving flaky, slow, or brittle tests
- Establishing testing conventions for a Go project
- Preparing testing workflows for CI or pre-merge verification

Do not use this skill as the primary reference for the full Testify API when the task is specifically about `assert`, `require`, `mock`, or `suite` usage in depth; use `golang-stretchr-testify` for that.

## Core Principles

1. Test observable behavior, not incidental implementation details
2. Keep unit tests fast and deterministic
3. Name scenarios clearly, especially in table-driven tests
4. Isolate external dependencies in unit tests
5. Separate integration tests from unit tests explicitly
6. Treat flaky tests as defects, not background noise
7. Use race detection and tooling as part of normal verification

## Best-Practice Summary

1. Table-driven tests should use named subtests via `t.Run`
2. Integration tests should be separated clearly, often with build tags or explicit environment setup
3. Tests should not depend on execution order
4. Independent tests should use `t.Parallel()` where safe
5. Prefer behavior and contract assertions over internal-state coupling
6. Packages with goroutines may benefit from leak detection such as `goleak`
7. Mock interfaces, not concrete types
8. Keep unit tests small and fast; reserve external systems for integration tests
9. Run tests with race detection in CI for concurrency-sensitive code
10. Use examples as executable documentation where they help users

## Test Structure and Organization

### File Conventions

```go
// package_test.go - tests in same package (white-box)
package mypackage

// mypackage_test.go - tests in external test package (black-box)
package mypackage_test
```

### Naming Conventions

```go
func TestAdd(t *testing.T) { ... }
func TestMyStruct_MyMethod(t *testing.T) { ... }
func BenchmarkAdd(b *testing.B) { ... }
func ExampleAdd() { ... }
func FuzzAdd(f *testing.F) { ... }
```

## Table-Driven Tests

Table-driven tests are idiomatic Go. Name each case so failures remain readable:

```go
func TestCalculatePrice(t *testing.T) {
    tests := []struct {
        name      string
        quantity  int
        unitPrice float64
        expected  float64
    }{
        {name: "single item", quantity: 1, unitPrice: 10.0, expected: 10.0},
        {name: "bulk discount", quantity: 100, unitPrice: 10.0, expected: 900.0},
        {name: "zero quantity", quantity: 0, unitPrice: 10.0, expected: 0.0},
    }

    for _, tt := range tests {
        tt := tt
        t.Run(tt.name, func(t *testing.T) {
            got := CalculatePrice(tt.quantity, tt.unitPrice)
            if got != tt.expected {
                t.Errorf("CalculatePrice(%d, %.2f) = %.2f, want %.2f",
                    tt.quantity, tt.unitPrice, got, tt.expected)
            }
        })
    }
}
```

## Unit Tests

Good unit tests are:

- fast
- isolated
- deterministic
- focused on one behavior at a time

Avoid reaching into databases, network services, clocks, or filesystem state unless that external dependency is the thing under test.

## HTTP Handler Testing

Use `httptest` for request/response testing. For request bodies, headers, query strings, and response assertions, see [HTTP Testing](./references/http-testing.md).

## Goroutine Leak Detection

For concurrent packages, leak detection can catch background goroutines that outlive the test:

```go
import (
    "testing"
    "go.uber.org/goleak"
)

func TestMain(m *testing.M) {
    goleak.VerifyTestMain(m)
}
```

Per-test usage is also possible with `goleak.VerifyNone(t)`.

## Deterministic Time and Concurrency Tests

For time-sensitive code, avoid real sleeps when a fake clock or deterministic concurrency helper will do. `testing/synctest` may help for newer Go versions, but stable alternatives such as fake clocks are often a better default for long-lived codebases.

See [Mocking](./references/mocking.md) for time-mocking examples.

## Test Timeouts

When a test may hang, use timeout helpers and make failures point at the real caller. See [Helpers](./references/helpers.md).

## Benchmarks

Benchmarks are useful for understanding performance-sensitive code paths and catching regressions, but they should not replace correctness tests.

```go
func BenchmarkStringConcatenation(b *testing.B) {
    b.Run("plus-operator", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            result := "a" + "b" + "c"
            _ = result
        }
    })

    b.Run("strings.Builder", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            var builder strings.Builder
            builder.WriteString("a")
            builder.WriteString("b")
            builder.WriteString("c")
            _ = builder.String()
        }
    })
}
```

Use input-size sub-benchmarks where scale matters.

## Parallel Tests

Use `t.Parallel()` when test cases are truly independent and shared fixtures are safe:

```go
func TestParallelOperations(t *testing.T) {
    tests := []struct {
        name string
        data []byte
    }{
        {"small data", make([]byte, 1024)},
        {"medium data", make([]byte, 1024*1024)},
    }

    for _, tt := range tests {
        tt := tt
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel()
            result := Process(tt.data)
            if result == nil {
                t.Fatal("expected non-nil result")
            }
        })
    }
}
```

## Fuzzing

Use fuzzing to expose parser edge cases, invariants, and crash conditions:

```go
func FuzzReverse(f *testing.F) {
    f.Add("hello")
    f.Add("")
    f.Add("a")

    f.Fuzz(func(t *testing.T, input string) {
        reversed := Reverse(input)
        doubleReversed := Reverse(reversed)
        if input != doubleReversed {
            t.Errorf("Reverse(Reverse(%q)) = %q, want %q", input, doubleReversed, input)
        }
    })
}
```

## Examples as Documentation

Examples are executable documentation verified by `go test`:

```go
func ExampleCalculatePrice() {
    price := CalculatePrice(100, 10.0)
    fmt.Printf("Price: %.2f\n", price)
    // Output: Price: 900.00
}
```

## Coverage

Coverage is a signal, not the goal:

```bash
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
go tool cover -func=coverage.out
```

Use low coverage to find untested risk, not as a reason to add low-value tests.

## Integration Tests

Separate integration tests from unit tests explicitly:

```go
//go:build integration

package mypackage

func TestDatabaseIntegration(t *testing.T) {
    // real database test setup
}
```

Run them separately:

```bash
go test -tags=integration ./...
```

For Docker Compose fixtures, schemas, and integration test structure, see [Integration Testing](./references/integration-testing.md).

## Mocking

Mock interfaces, not concrete types. Define interfaces at the point of consumption when possible.

For mock patterns, fixtures, and time mocking, see [Mocking](./references/mocking.md).

## Enforce with Linters

Several test best practices can be reinforced automatically with linters such as `thelper`, `paralleltest`, and `testifylint`. Use `golang-lint` for lint-policy guidance.

## Quick Reference

```bash
go test ./...
go test -run TestName ./...
go test -run TestName/subtest ./...
go test -race ./...
go test -cover ./...
go test -bench=. -benchmem ./...
go test -fuzz=FuzzName ./...
go test -tags=integration ./...
```

## Cross-References

- Use `golang-stretchr-testify` for detailed `assert`, `require`, `mock`, and `suite` guidance
- Use `golang-troubleshooting` when tests are failing for unclear runtime reasons or flaking under concurrency
- Use `golang-lint` when test quality is tied to lint configuration and enforcement
- Use `test-driven-development` when the goal is driving implementation from failing tests rather than just improving a test suite

## Common Pitfalls

1. Writing tests that lock in implementation details instead of behavior
2. Letting integration tests silently become unit-test dependencies
3. Ignoring flaky tests rather than isolating and fixing them
4. Using real time and sleeps where deterministic control is possible
5. Treating coverage percentage as a substitute for test quality

## Verification Checklist

- [ ] The description starts with `Use when ...`
- [ ] The guidance emphasizes behavior, determinism, and maintainability
- [ ] Cross-references point only to local skills
- [ ] The reference docs still cover HTTP testing, helpers, mocking, and integration structure
- [ ] The workflow guidance supports both local development and CI
