# Test Helpers

## Test Timeout

For tests that may hang, use a timeout helper that panics with caller location:

Prefer `go test -timeout` for whole-package limits and `t.Context()` (Go 1.24+) with `context.WithTimeout` for per-operation limits. Use this helper only when you want a hard panic with the caller location. Imports: fmt, runtime, strconv, testing, time.

```go
// Pattern discussed in stretchr/testify issue #1101
func testWithTimeout(t *testing.T, timeout time.Duration) {
    t.Helper()

    testFinished := make(chan struct{})
    t.Cleanup(func() {
        close(testFinished)
    })

    var pc [1]uintptr
    n := runtime.Callers(2, pc[:])
    line, funcName := "", ""
    if n > 0 {
        frames := runtime.CallersFrames(pc[:])
        frame, _ := frames.Next()
        line = frame.File + ":" + strconv.Itoa(frame.Line)
        funcName = frame.Function
    }

    go func() {
        select {
        case <-testFinished:
        case <-time.After(timeout):
            panic(fmt.Sprintf("%s: Test timed out after: %v\n%s", funcName, timeout, line))
        }
    }()
}

// Usage
func TestLongRunningOperation(t *testing.T) {
    testWithTimeout(t, 2*time.Second)
    _ = LongRunningOperation() // or check its error
    // If this takes longer than 2 seconds, the test panics with location info
}
```
