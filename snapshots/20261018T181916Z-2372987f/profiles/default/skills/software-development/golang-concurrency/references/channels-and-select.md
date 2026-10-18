# Channels and Select Patterns

## Goroutine Lifecycle

NEVER start a goroutine without knowing how it stops. Every goroutine MUST answer: **how will it stop?**

```go
// ✗ Bad — fire-and-forget, no way to stop or wait
func startWorker() {
    go func() {
        for {
            doWork() // runs forever, leaks on shutdown
        }
    }()
}

// ✓ Good — goroutine respects context cancellation, caller can wait
func startWorker(ctx context.Context) <-chan struct{} {
    done := make(chan struct{})
    go func() {
        defer close(done)
        for {
            select {
            case <-ctx.Done():
                return
            default:
                doWork(ctx)
            }
        }
    }()
    return done // closed when the worker exits
}
```

### Panic Recovery at Goroutine Boundaries

A panic in a goroutine crashes the entire process. Recover only where you can handle or report it (request handlers, worker supervisors, background-job runners). Log with the stack, then fail that unit of work or re-panic; never silently swallow a panic:

```go
// imports: context, log/slog, runtime/debug
go func() {
    defer func() {
        if r := recover(); r != nil {
            slog.Error("background task panicked", "panic", r, "stack", string(debug.Stack()))
        }
    }()
    doWork(ctx)
}()
```

## Channel Direction

Specify direction in function signatures to prevent misuse at compile time:

```go
// ✗ Bad — bidirectional: the callee could accidentally send on or close a channel it should only read
func consume(ch chan int) { ... }

// ✓ Good — compiler enforces correct usage
func produce(ch chan<- int) { ... } // send-only
func consume(ch <-chan int) { ... } // receive-only
```

## Channel Closing

Channels MUST be closed by the sender (producer), NEVER by the receiver — it causes a panic if the sender writes after close.

```go
// ✓ Good — producer closes when done
func generate(ctx context.Context) <-chan int {
    ch := make(chan int)
    go func() {
        defer close(ch) // sender closes
        for i := 0; ; i++ {
            select {
            case ch <- i:
            case <-ctx.Done():
                return
            }
        }
    }()
    return ch
}
```

## Buffer Size

| Size | When to use |
| --- | --- |
| 0 (unbuffered) | Default. Synchronizes sender and receiver — use when you need handoff guarantees |
| 1 | Signal channels (`done := make(chan struct{}, 1)`), or when sender must not block on a single pending item |
| N > 1 | Only with measured justification — document why N was chosen and what happens when the buffer fills |

```go
// ✓ Good — unbuffered for synchronous handoff
ch := make(chan Result)

// ✓ Good — buffered 1 for signal
done := make(chan struct{}, 1)

// ✗ Suspicious — arbitrary large buffer hides backpressure problems
// Give explanation in comments.
ch := make(chan Task, 1000) // why 1000? what if it fills?
```

## Select for Non-Blocking Communication

Use `select` to multiplex channel operations and always include `ctx.Done()` to prevent goroutine leaks:

```go
func process(ctx context.Context, in <-chan Task, out chan<- Result) {
    for {
        select {
        case <-ctx.Done():
            return
        case task, ok := <-in:
            if !ok {
                return // channel closed
            }
            result := handle(ctx, task)
            select {
            case out <- result:
            case <-ctx.Done():
                return
            }
        }
    }
}
```

## Avoid `time.After` in Hot Loops

Before Go 1.23, each `time.After` timer stayed live until it fired (a leak in loops). Since Go 1.23 (when the module's `go` line is ≥ 1.23), unreferenced timers are garbage-collected, but each iteration still allocates a timer, so reuse one in hot paths. Also from 1.23, `Stop`/`Reset` guarantee no stale value is received afterwards (timer channels are effectively unbuffered).

```go
// ✗ Avoid in hot loops — allocates a timer per iteration (leaks until it fires on Go < 1.23)
for {
    select {
    case msg := <-ch:
        handle(msg)
    case <-time.After(5 * time.Second): // new timer every loop — leak
        handleTimeout()
    }
}

// ✓ Good (go.mod go >= 1.23) — reuse the timer; no drain needed
timer := time.NewTimer(5 * time.Second)
defer timer.Stop()
for {
    select {
    case msg := <-ch:
        timer.Reset(5 * time.Second)
        handle(msg)
    case <-timer.C:
        handleTimeout()
        timer.Reset(5 * time.Second)
    }
}
```

On go.mod `go` < 1.23, drain before `Reset` after a message:

```go
if !timer.Stop() {
    select {
    case <-timer.C:
    default:
    }
}
timer.Reset(5 * time.Second)
```
