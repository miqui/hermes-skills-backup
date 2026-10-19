# Memory Safety Security Rules

Memory safety vulnerabilities can lead to crashes, data corruption, and security compromises.

**Rules:**

1. Integer overflow MUST be checked at boundaries — NEVER trust unchecked arithmetic on external input.
2. `unsafe` MUST NOT be used in application code — restrict to low-level libraries with thorough review.
3. Data races MUST be detected with `-race` flag in CI.

---

## Integer Overflow — High

Integer overflows can cause unexpected behavior and crashes.

**Bad:**

```go
func allocateBuffer(rows, cols int) []byte {
    size := rows * cols  // DON'T: Can overflow
    return make([]byte, size)
}
```

**Good:**

```go
import "math"

func safeMultiply(a, b int) (int, error) {
    if a == 0 || b == 0 {
        return 0, nil
    }
    if a < 0 || b < 0 {
        return 0, errors.New("negative size")
    }
    if a > math.MaxInt/b { // math.MaxInt matches int on 32- and 64-bit platforms
        return 0, errors.New("integer overflow")
    }
    return a * b, nil
}

func allocateBuffer(rows, cols int) ([]byte, error) {
    size, err := safeMultiply(rows, cols)
    if err != nil {
        return nil, err
    }
    const maxBufferSize = 100 * 1024 * 1024 // 100MB limit
    if size > maxBufferSize {
        return nil, errors.New("buffer size exceeds limit")
    }
    return make([]byte, size), nil
}
```

---

## math/big.Rat Issues — Low

Rat can consume large amounts of memory if denominators grow without bounds.

**Bad:**

```go
import "math/big"

func unsafeFraction(operations int) *big.Rat {
    r := big.NewRat(1, 1)
    for i := 0; i < operations; i++ {
        r.Mul(r, big.NewRat(int64(i+1), int64(i+2)))  // DON'T
    }
    return r  // Could be memory intensive
}
```

**Good:**

```go
const maxRatNumBits = 1000

func safeFraction(operations int) (*big.Rat, error) {
    r := big.NewRat(1, 1)
    for i := 0; i < operations; i++ {
        r.Mul(r, big.NewRat(int64(i+1), int64(i+2)))
        if r.Num().BitLen() > maxRatNumBits || r.Denom().BitLen() > maxRatNumBits {
            return nil, errors.New("fraction precision too large")
        }
    }
    return r, nil
}
```

---

## Retained Sub-slices and Shared Slices — Medium

`copy()` has memmove semantics and handles overlapping slices correctly, so overlap is not a hazard. The real slice hazards are:

- A small sub-slice keeps the whole backing array alive (memory retention; may keep sensitive data in memory).
- Sharing a slice across goroutines without synchronization is a data race.

**Bad:**

```go
func header(buf []byte) []byte {
    return buf[:16] // DON'T: retains the entire backing array (e.g. a large request body)
}
```

**Good:**

```go
import "slices"

func header(buf []byte) []byte {
    return slices.Clone(buf[:16]) // or append([]byte(nil), buf[:16]...)
}
```

---

## Use of unsafe Package — High

The unsafe package bypasses Go's type safety and memory safety.

**Bad:**

```go
import "unsafe"

func UnsafeStringToBytes(s string) []byte {
    return (*[0x7fffffff]byte)(unsafe.Pointer(
        (*reflect.StringHeader)(unsafe.Pointer(&s)).Data, // DON'T: reflect.StringHeader is deprecated
    ))[:len(s):len(s)]  // DON'T: memory corruption risk
}

func TypePun(value uint64) float64 {
    return *(*float64)(unsafe.Pointer(&value))  // DON'T
}
```

**Good:**

```go
// Safe string encoding
func StringToBytes(s string) []byte {
    return []byte(s)
}
func BytesToString(b []byte) string {
    return string(b)
}

// Safe type conversion
func Uint64ToFloat64(value uint64) float64 {
    return math.Float64frombits(value)
}

// If unsafe is truly needed (profiled hot path, strings never mutated), use the
// Go 1.20+ helpers instead of reflect headers: unsafe.String, unsafe.StringData,
// unsafe.Slice.
```

---

## Data Races — High

Go's race detector is your primary defense.

**Bad:**

```go
type Counter struct {
    value int
}

func (c *Counter) Increment() {
    c.value++  // DON'T: Data race without sync
}
```

**Good:**

```go
import "sync"

type Counter struct {
    value int
    mu    sync.Mutex
}

func (c *Counter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.value++
}

// Or atomic for simple cases
import "sync/atomic"
type AtomicCounter struct {
    value int64
}
func (c *AtomicCounter) Increment() {
    atomic.AddInt64(&c.value, 1)
}
```

## Always Run Race Detector

```bash
go test -race ./...
go build -race
```

---

## CWE References

- **CWE-190**: Integer Overflow or Wraparound
- **CWE-119**: Improper Restriction of Operations within Bounds
- **CWE-125**: Out-of-bounds Read
- **CWE-787**: Out-of-bounds Write
- **CWE-362**: Race Condition
- **CWE-367**: Time-of-check Time-of-use (TOCTOU)
