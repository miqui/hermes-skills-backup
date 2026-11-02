# Network/Web Security Rules

Network and web security vulnerabilities can lead to data leakage and unauthorized access.

**Rules:**

1. Redirects MUST be validated against an allowlist of domains.
2. HTTP servers MUST configure `ReadHeaderTimeout`, `ReadTimeout`, `WriteTimeout`, and `IdleTimeout`.
3. Pprof endpoints MUST NEVER be exposed publicly.
4. XML input MUST be size-limited and decoded into concrete types. Go's `encoding/xml` does not resolve external entities; XXE applies to libxml2 bindings (cgo).

---

## Open Redirect Vulnerability — Medium

Redirects to unvalidated URLs can be used for phishing.

**Bad:**

```go
target := r.URL.Query().Get("url")
http.Redirect(w, r, target, http.StatusFound) // DON'T
```

**Good:**

```go
target := r.URL.Query().Get("url")
u, err := url.Parse(target)
if err != nil {
    return errors.New("invalid url")
}
// Only allow http/https
if u.Scheme != "http" && u.Scheme != "https" {
    return errors.New("invalid scheme")
}
// Block javascript/data schemes
if strings.HasPrefix(target, "javascript:") || strings.HasPrefix(target, "data:") {
    return errors.New("blocked scheme")
}
// Check against whitelist
if !isAllowedDomain(u.Host) {
    return errors.New("invalid domain")
}
http.Redirect(w, r, target, http.StatusFound)
```

---

## Bind to All Interfaces — Medium

Binding to 0.0.0.0 exposes services to all network interfaces.

**Bad:**

```go
listener, _ := net.Listen("tcp", "0.0.0.0:8080") // DON'T: Exposes all interfaces
```

**Good:**

```go
// Bind only to localhost
listener, _ := net.Listen("tcp", "127.0.0.1:8080")

// Or specific internal IP
listener, _ := net.Listen("tcp", "10.0.1.5:8080")
```

---

## Slowloris Attack Vulnerability — Medium

Slowloris attacks exhaust connection pools.

**Bad:**

```go
server := &http.Server{
    Addr: ":8080",
    // Missing ReadHeaderTimeout, ReadTimeout, WriteTimeout, IdleTimeout
}
```

**Good:**

```go
server := &http.Server{
    Addr:              ":8080",
    ReadHeaderTimeout: 5 * time.Second, // Slowloris defense even if ReadTimeout is unset
    ReadTimeout:       5 * time.Second,
    WriteTimeout:      10 * time.Second,
    IdleTimeout:       120 * time.Second,
    MaxHeaderBytes:    1 << 20, // Limit header size to 1MB
}

// Bound request bodies in handlers:
r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
```

---

## Insecure HTTP Server Configuration — Medium

Running HTTP servers without proper security settings.

**Bad:**

```go
http.ListenAndServe(":8080", handler) // DON'T: No security hardening
```

**Good:**

```go
server := &http.Server{
    Addr:              ":443",
    ReadHeaderTimeout: 5 * time.Second,
    ReadTimeout:       5 * time.Second,
    WriteTimeout:      10 * time.Second,
    IdleTimeout:       120 * time.Second,
    MaxHeaderBytes:    1 << 20,
}
server.ListenAndServeTLS("cert.pem", "key.pem")
```

---

## Observable Timing (Timing Attacks) — Medium

Timing differences can leak sensitive information.

**Bad:**

```go
func checkPassword(input, secret string) bool {
    return input == secret // DON'T: Short-circuit comparison leaks timing
}
```

**Good:**

```go
import "crypto/subtle"

// For comparing tokens, MACs, or hashes (same-length values):
func checkToken(input, expected string) bool {
    return subtle.ConstantTimeCompare([]byte(input), []byte(expected)) == 1
}

// subtle.ConstantTimeCompare returns immediately when lengths differ, so it
// still leaks length. If the length is secret, hash both sides first:
func checkSecretLen(input, expected string) bool {
    a, b := sha256.Sum256([]byte(input)), sha256.Sum256([]byte(expected))
    return subtle.ConstantTimeCompare(a[:], b[:]) == 1
}

// For passwords, use Argon2id (preferred) or bcrypt:
// - bcrypt.CompareHashAndPassword compares in constant time.
// - argon2.IDKey only derives a key. Store salt + params, re-derive from the
//   candidate password, and compare the derived keys yourself:
//     key := argon2.IDKey([]byte(password), salt, 3, 64*1024, 4, 32)
//     ok := subtle.ConstantTimeCompare(key, storedKey) == 1
// - bcrypt: err := bcrypt.CompareHashAndPassword([]byte(storedHash), []byte(password))

// For HMAC verification:
import "crypto/hmac"
func verifyHMAC(message, messageMAC, key []byte) bool {
    mac := hmac.New(sha256.New, key)
    mac.Write(message)
    expectedMAC := mac.Sum(nil)
    return hmac.Equal(messageMAC, expectedMAC) // Constant-time
}
```

---

## Exposed pprof Profiling Endpoints — High

Debug pprof endpoints expose sensitive runtime information.

**Bad:**

```go
import _ "net/http/pprof" // DON'T: registers /debug/pprof on http.DefaultServeMux
http.ListenAndServe(":8080", nil) // nil handler = DefaultServeMux, so pprof is exposed
// (with a custom mux, the blank import alone does not expose it)
```

**Good:**

```go
// Option 1: Use build tags to exclude pprof from production builds
// File: debug_pprof.go
//go:build !production

package main

import _ "net/http/pprof"
```

```go
// Option 2: Serve pprof on a separate internal-only listener
// Requires a named import (not blank); imports shown for completeness.
import (
    "net/http"
    "net/http/pprof"
)

func startDebugServer() {
    debugMux := http.NewServeMux()
    debugMux.HandleFunc("/debug/pprof/", pprof.Index)
    debugMux.HandleFunc("/debug/pprof/cmdline", pprof.Cmdline)
    debugMux.HandleFunc("/debug/pprof/profile", pprof.Profile)
    debugMux.HandleFunc("/debug/pprof/symbol", pprof.Symbol)
    debugMux.HandleFunc("/debug/pprof/trace", pprof.Trace)
    go http.ListenAndServe("127.0.0.1:6060", debugMux) // localhost only
}
```

---

## XML Input Limits (XXE) — Medium

Go's `encoding/xml` does not resolve external entities, so classic XXE does not apply. The risks are resource exhaustion from large or deeply nested input, and XXE in libxml2 bindings (cgo).

**Bad:**

```go
decoder := xml.NewDecoder(r.Body)
decoder.Decode(&person) // DON'T: unbounded input
```

**Good:**

```go
r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
decoder := xml.NewDecoder(r.Body)
decoder.Strict = true
var person Person // decode into a concrete type
if err := decoder.Decode(&person); err != nil {
    return err
}
// If using a cgo libxml2 binding, disable DTD/entity loading in that library.
```

---

## Permissive Regex Validation — Low

Weak regex validation can allow malicious input.

**Bad:**

```go
matched, _ := regexp.MatchString(`.+@.+\..+`, email) // DON'T: Too permissive
```

**Good:**

```go
var emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
if !emailRegex.MatchString(email) {
    return errors.New("invalid email")
}
// Also block injection patterns
```

---

## CWE References

- **CWE-601**: Open Redirect
- **CWE-208**: Observable Timing Discrepancy
- **CWE-611**: Improper Restriction of XML External Entity Reference
- **CWE-770**: Allocation of Resources Without Limits
- **CWE-20**: Improper Input Validation
- **CWE-200**: Exposure of Sensitive Information
