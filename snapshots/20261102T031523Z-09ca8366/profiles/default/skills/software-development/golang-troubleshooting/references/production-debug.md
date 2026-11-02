# Production Debugging

## Production Debugging Checklist

When paged for a production issue:

### Step 1: Capture Immediately (don't restart!)

Capture all profiles before restarting the process. Use the curl commands from [pprof.md](./pprof.md), targeting your production server address. At minimum, capture: goroutine dump (`?debug=2`), heap, CPU (30s), and mutex profiles.

### Step 2: System Metrics

```bash
ps aux | grep myapp
lsof -p PID | wc -l       # file descriptors
ss -s                       # socket summary
netstat -an | grep ESTABLISHED | wc -l
```

### Step 3: Analyze Locally

Download the captured `.prof` files and analyze with `go tool pprof` (see [pprof.md](./pprof.md)).

### Optional: Flight Recorder (Go 1.25+)

`runtime/trace.FlightRecorder` keeps a rolling in-memory window of the execution trace so you can dump the seconds *before* an incident (e.g. a slow request or SLO breach) instead of tracing continuously:

```go
fr := trace.NewFlightRecorder(trace.FlightRecorderConfig{
    MinAge:   5 * time.Second, // keep at least this much history
    MaxBytes: 16 << 20,        // upper bound hint; takes precedence over MinAge
})
if err := fr.Start(); err != nil { log.Fatal(err) }
defer fr.Stop()

// On a trigger (slow request, error spike):
f, _ := os.Create("incident.trace")
defer f.Close()
if _, err := fr.WriteTo(f); err != nil { log.Printf("flight recorder dump: %v", err) }
// Analyze: go tool trace incident.trace
```

Only one flight recorder may be active at a time. Treat dumps as sensitive (they contain stacks and goroutine data), and rate-limit triggers.

---

## Logging & Observability

### Strategic Log Placement

Place logs at **component boundaries**, not sprinkled randomly. The goal is to see data entering and exiting each layer, so you can identify exactly which component corrupts or drops it:

```go
// 1. Function entry/exit with key parameters
func ProcessOrder(ctx context.Context, orderID string) error {
    log.Printf("ProcessOrder: start orderID=%s", orderID)
    defer log.Printf("ProcessOrder: done orderID=%s", orderID)
    // ...
}

// 2. Before and after external calls
log.Printf("calling payment API for order %s", orderID)
resp, err := paymentClient.Charge(ctx, req)
log.Printf("payment API: status=%d err=%v", resp.StatusCode, err)

// 3. At decision points
if user.IsAdmin {
    log.Printf("admin path for user %s", user.ID)
}
```

### Structured Logging (Go 1.21+)

```go
import "log/slog"

slog.Info("processing request",
    "method", r.Method,
    "path", r.URL.Path,
    "user_id", userID,
)

slog.Error("database query failed",
    "err", err,
    "query", query,
    "duration_ms", elapsed.Milliseconds(),
)
```

### Request ID Tracing

```go
type ctxKey string

func WithRequestID(ctx context.Context, id string) context.Context {
    return context.WithValue(ctx, ctxKey("request_id"), id)
}

func RequestID(ctx context.Context) string {
    id, _ := ctx.Value(ctxKey("request_id")).(string)
    return id
}
```

---

## Network & HTTP Debugging

### HTTP Client Issues

```go
// 1. Always set timeouts — default http.Client has NO timeout
client := &http.Client{
    Timeout: 30 * time.Second,
    Transport: &http.Transport{
        DialContext:          (&net.Dialer{Timeout: 5 * time.Second}).DialContext,
        TLSHandshakeTimeout: 5 * time.Second,
        IdleConnTimeout:     90 * time.Second,
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 10,
    },
}

// 2. Always close response body
resp, err := client.Do(req)
if err != nil {
    return err
}
defer resp.Body.Close()

// 3. Read body on error status (for error messages from server)
if resp.StatusCode >= 400 {
    body, _ := io.ReadAll(resp.Body)
    return fmt.Errorf("API error %d: %s", resp.StatusCode, body)
}

// 4. Dump full request/response for debugging
import "net/http/httputil"
dump, _ := httputil.DumpRequestOut(req, true)
log.Printf("request:\n%s", dump)
dump, _ = httputil.DumpResponse(resp, true)
log.Printf("response:\n%s", dump)
```
