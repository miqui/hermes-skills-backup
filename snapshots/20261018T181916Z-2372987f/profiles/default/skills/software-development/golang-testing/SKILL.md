---
name: golang-testing
description: "Use when writing, reviewing, or improving Go tests, including unit tests, integration tests, table-driven tests, fuzzing, concurrency-sensitive tests, benchmark scaffolding, and test-suite design."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [golang, go, testing, unit-tests, integration-tests, fuzzing, benchmarks]
    related_skills: [golang-stretchr-testify, golang-lint, golang-troubleshooting]
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

Go 1.22+ scopes loop variables per iteration, so `tt := tt` is unnecessary (keep it only when go.mod says `go` < 1.22).

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

This is the canonical home for `goleak` guidance (`golang-concurrency` links here). For concurrent packages, leak detection catches background goroutines that outlive the test:

```go
import (
    "testing"
    "go.uber.org/goleak"
)

func TestMain(m *testing.M) {
    goleak.VerifyTestMain(m)
}
```

Per-test usage is also possible with `goleak.VerifyNone(t)`, but do not combine it with `t.Parallel()` tests (other tests' goroutines show up as leaks); prefer `VerifyTestMain` there. Inside a `synctest` bubble, the runtime already fails the test if goroutines stay blocked, so goleak is redundant.

## Deterministic Time and Concurrency Tests

For time-sensitive code, avoid real sleeps. On Go 1.25+, `testing/synctest` is generally available: `synctest.Test(t, func(t *testing.T) {...})` runs the body in an isolated "bubble" with a fake clock that advances when all goroutines are blocked, and `synctest.Wait()` blocks until every other goroutine in the bubble is durably blocked. (Go 1.24 only had an experimental `synctest.Run` behind `GOEXPERIMENT=synctest`.)

```go
// imports: testing, testing/synctest, time
func TestTimeout(t *testing.T) {
    synctest.Test(t, func(t *testing.T) {
        done := make(chan struct{})
        go func() {
            time.Sleep(time.Hour) // fake time: returns instantly
            close(done)
        }()
        synctest.Wait()
        select {
        case <-done:
            t.Fatal("finished too early")
        default:
        }
        time.Sleep(time.Hour)
        <-done
    })
}
```

Bubble limits: real network I/O is not "durably blocking" (use `net.Pipe` or fakes); every goroutine started in the bubble must exit before the function returns; `t.Cleanup` and `t.Context()` are scoped to the bubble.

On older Go versions, or when you need an injectable `Clock` interface, use a fake clock. See [Mocking](./references/mocking.md).

## Test Context, Dirs, and Env

- `t.Context()` (Go 1.24+): context cancelled just before `Cleanup` functions run; use it for goroutines and clients started by the test
- `t.TempDir()`: per-test temporary directory, removed automatically
- `t.Setenv(k, v)`: restores the env var on cleanup (cannot be used with `t.Parallel()`)
- `t.Chdir(dir)` (Go 1.24+): changes working directory for the test and restores it (also not parallel-safe)

## Test Timeouts

When a test may hang, use timeout helpers and make failures point at the real caller. See [Helpers](./references/helpers.md).

## Benchmarks

Benchmarks are useful for understanding performance-sensitive code paths and catching regressions, but they should not replace correctness tests.

Go 1.24+: use `for b.Loop() { ... }`. Setup before the loop is excluded from timing, and the compiler is prevented from optimizing away the loop body's calls. On go < 1.24 use `for i := 0; i < b.N; i++`.

```go
// imports: strings, testing
var (
    parts = strings.Split(strings.Repeat("abc,", 100), ",") // runtime input, not a constant
    sink  string                                            // package-level sink defeats dead-code elimination
)

func BenchmarkConcat(b *testing.B) {
    b.Run("plus-operator", func(b *testing.B) {
        for b.Loop() {
            s := ""
            for _, p := range parts {
                s += p
            }
            sink = s
        }
    })

    b.Run("strings.Builder", func(b *testing.B) {
        for b.Loop() {
            var builder strings.Builder
            for _, p := range parts {
                builder.WriteString(p)
            }
            sink = builder.String()
        }
    })
}
```

Avoid constant operands (e.g. `"a" + "b" + "c"`): the compiler folds them at build time and the benchmark measures nothing. Feed runtime inputs and keep results alive via a sink; on go < 1.24 this is required with `b.N` loops too.

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
go test -shuffle=on ./...   # Go 1.17+: randomize test order; a failing run prints the seed, rerun with -shuffle=<seed>
go test -cover ./...
go test -bench=. -benchmem ./...
go test -fuzz=FuzzName ./...
go test -tags=integration ./...
```

## Cross-References

- Use `golang-stretchr-testify` for detailed `assert`, `require`, `mock`, and `suite` guidance
- Use `golang-troubleshooting` when tests are failing for unclear runtime reasons or flaking under concurrency
- Use `golang-lint` when test quality is tied to lint configuration and enforcement

## Common Pitfalls

1. Writing tests that lock in implementation details instead of behavior
2. Letting integration tests silently become unit-test dependencies
3. Ignoring flaky tests rather than isolating and fixing them
4. Using real time and sleeps where deterministic control is possible
5. Treating coverage percentage as a substitute for test quality

## Verification Checklist

- [ ] `go test -race ./...` passes; goroutine-spawning packages use `goleak`
- [ ] `go test -shuffle=on ./...` passes (no hidden test-order dependence)
- [ ] Table-driven cases are named subtests; no `tt := tt` on Go 1.22+
- [ ] No real sleeps or wall-clock dependence (fake clock or `synctest`)
- [ ] Integration tests sit behind a build tag or explicit env gate
- [ ] Tests use `t.TempDir`/`t.Setenv`/`t.Context` instead of manual cleanup
