---
name: golang-concurrency
description: "Use when writing or reviewing concurrent Go code involving goroutines, channels, select, sync primitives, errgroup, worker pools, fan-out or fan-in pipelines, cancellation, and leak-free shutdown behavior."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [golang, go, concurrency, goroutines, channels, synchronization, errgroup]
    related_skills: [golang-troubleshooting, golang-testing, golang-lint]
---

# Go Concurrency

## Overview

This skill covers structured concurrency in Go: how to spawn goroutines safely, choose between channels and locks, propagate cancellation, bound parallelism, and avoid leaks, deadlocks, races, and invisible shared-state bugs.

The guiding principle is that every goroutine is a resource with a lifecycle. Concurrency should make ownership, shutdown, and error propagation clearer — not more implicit.

## When to Use

- Writing or reviewing concurrent Go code
- Choosing between channels, mutexes, atomics, `sync.Map`, or `errgroup`
- Designing worker pools, pipelines, fan-out/fan-in stages, or cancellation behavior
- Diagnosing goroutine leaks, deadlocks, missing shutdown paths, or misuse of shared state
- Auditing whether concurrency is actually justified in a code path

Do not use this skill as the primary reference for post-facto debugging of a live failure when the main need is investigation workflow rather than concurrency design; use `golang-troubleshooting` for that.

## Core Principles

1. Every goroutine must have a clear exit path
2. Concurrency should preserve ownership clarity, not hide it
3. Cancellation should be explicit and easy to propagate
4. Shared mutable state should be minimized
5. Buffers and parallelism limits should be justified, not guessed
6. Tests should detect races and leaks before production does

## Concurrency Checklist

Before spawning a goroutine, answer:

- [ ] How does it stop?
- [ ] Who can cancel it?
- [ ] Who waits for it?
- [ ] What owns any channels involved?
- [ ] Does this really need to be concurrent?

## Channels vs Mutex vs Atomic

| Scenario | Preferred tool | Why |
| --- | --- | --- |
| Passing ownership or work between goroutines | Channel | Makes communication explicit |
| Coordinating lifecycle or shutdown | Channel + context | Select-based cancellation and clean exit |
| Protecting shared fields | `sync.Mutex` / `sync.RWMutex` | Straightforward critical sections |
| Simple counters or flags | `sync/atomic` | Cheap, explicit, low-level synchronization |
| Read-heavy concurrent map access | `sync.Map` | Useful in some read-heavy patterns |
| Deduplicating concurrent work | `singleflight` | Prevents duplicate expensive calls |
| Waiting for goroutines with error handling | `errgroup` | Structured fan-out with cancellation support |

## WaitGroup vs errgroup

| Need | Use | Why |
| --- | --- | --- |
| Wait only | `sync.WaitGroup` | Minimal coordination |
| Wait + first error | `errgroup.Group` | Error propagation |
| Wait + sibling cancellation on error | `errgroup.WithContext` | Structured cancellation |
| Bounded concurrency | `errgroup.SetLimit(n)` | Simpler than many custom worker pools |

## Sync Primitives Quick Reference

| Primitive | Use case | Key note |
| --- | --- | --- |
| `sync.Mutex` | Shared mutable state | Keep critical sections short |
| `sync.RWMutex` | Many readers, few writers | Avoid upgrading read locks |
| `sync/atomic` | Simple counters/flags | Prefer typed atomics where available |
| `sync.Map` | Specialized concurrent map usage | Not a default replacement for `map` + lock; `Clear` exists since Go 1.23 |
| `sync.Pool` | Temporary object reuse | Reset objects before putting them back |
| `sync.Once` | One-time initialization | Prefer clear initialization boundaries |
| `sync.WaitGroup` | Wait for completion | Call `Add` before spawning, or use `wg.Go` (Go 1.25+) |
| `singleflight` | Deduplicate work | Useful for cache stampede control |
| `errgroup` | Task groups with errors | Preferred for many concurrent request flows |

For deeper examples, see [Sync Primitives Deep Dive](./references/sync-primitives.md).

## Channel Rules

- Only the sending side closes a channel, never the receiver. With multiple senders, a coordinator closes it after all senders finish (e.g. a `WaitGroup` goroutine, as in fan-in)
- Prefer explicit channel direction in function signatures
- Default to unbuffered channels unless a buffer is justified
- Avoid sending mutable shared pointers unless that sharing is intentional and protected
- Always decide what happens if the receiver stops early

For select patterns and channel examples, see [Channels and Select Patterns](./references/channels-and-select.md).

## Reacting to Cancellation with context.AfterFunc

`stop := context.AfterFunc(ctx, cleanup)` (Go 1.21+) runs `cleanup` in its own goroutine once `ctx` is done. Prefer it over a goroutine parked on `<-ctx.Done()` just to run cleanup.

- `stop()` returns `true` if it prevented `cleanup` from being started; `false` if it already started (or `stop` was already called). Call `stop()` (e.g. `defer stop()`) when the cleanup is no longer needed, so nothing is retained.
- Cleanup is NOT waited for. If the caller must know it finished, synchronize yourself (a `done` channel closed by `cleanup`).

```go
stop := context.AfterFunc(ctx, func() {
    defer close(done)
    conn.SetDeadline(time.Now()) // unblock a pending Read
})
defer stop()
```

## Pipelines and Worker Pools

Pipelines and worker pools are useful when work is naturally staged or bounded. They become dangerous when ownership is unclear or when backpressure is ignored.

Use them when:

- work can be split into independent units
- concurrency needs a clear upper bound
- cancellation must stop the whole flow predictably

See [Pipelines and Worker Pools](./references/pipelines.md) for fan-out/fan-in, bounded workers, and iterator-style patterns.

## Common Mistakes

| Mistake | Better approach |
| --- | --- |
| Fire-and-forget goroutine with no shutdown path | Add context, done signaling, or ownership-based waiting |
| Closing a channel from the receiver side | Only the sending side should close |
| Using `time.After` in a hot loop | Since Go 1.23 (go.mod `go` ≥ 1.23) unreferenced timers are GC'd, so it no longer leaks until firing, but it still allocates per iteration; reuse a `time.NewTimer` with `Reset`. On older versions it leaks |
| Missing `ctx.Done()` in a select | Always allow cancellation to unblock the goroutine |
| Unbounded goroutine spawning | Use a limit, semaphore, worker pool, or `errgroup.SetLimit` |
| Sharing mutable pointers through channels by accident | Send values or clearly synchronized shared references |
| Calling `wg.Add` inside a goroutine | Call `Add` before spawn, or use `wg.Go` (Go 1.25+) |
| Holding a mutex across I/O | Keep the lock boundary narrow |

## Auditing Concurrent Code

When reviewing a codebase, check for:

- goroutine spawns without a visible shutdown path
- channels with unclear ownership or closure rules
- missing context propagation
- shared mutable maps or state without synchronization
- use of timers, tickers, or background loops without cleanup
- tests that never run with `-race`
- tests that need goroutine-leak checks or fake-time control (see `golang-testing`: `goleak`, `testing/synctest` on Go 1.25+)

## Cross-References

- Use `golang-troubleshooting` when you need race/leak/deadlock investigation workflow
- Use `golang-testing` for concurrency-focused test design, fuzzing, and leak-detection patterns
- Use `golang-lint` when lint and static-analysis rules are part of concurrency quality enforcement

## References

- [Go Concurrency Patterns: Pipelines](https://go.dev/blog/pipelines)
- [Effective Go: Concurrency](https://go.dev/doc/effective_go#concurrency)

## Common Pitfalls

1. Adding concurrency before proving it improves the design or performance
2. Treating channels as automatically safer than locks without thinking about ownership
3. Forgetting that cancellation and cleanup are part of correctness
4. Assuming buffered channels solve backpressure instead of merely delaying it
5. Writing concurrent code without race detection and shutdown-oriented tests

## Verification Checklist

- [ ] Every goroutine has a stop path, an owner that waits for it, and ctx propagation
- [ ] Every channel has one clear closer (the sender, or a WaitGroup coordinator when there are several senders); every blocking send/receive selects on `ctx.Done()`
- [ ] Parallelism is bounded (`errgroup.SetLimit`, semaphore, or pool)
- [ ] `go test -race` passes; leak checks run for packages that spawn goroutines
- [ ] No lock is held across I/O or channel operations
