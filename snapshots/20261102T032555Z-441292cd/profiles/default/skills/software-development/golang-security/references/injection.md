# Injection Security Rules

Injection vulnerabilities allow attackers to execute arbitrary code, queries, or commands.

**Rules:**

1. SQL queries MUST use parameterized placeholders — NEVER concatenate user input.
2. Command execution MUST use `exec.Command` with separate args — NEVER shell interpolation.
3. HTML output MUST use `html/template` for automatic escaping.
4. SSRF: outbound URLs MUST be validated against an allowlist.

---

## SQL Injection — Critical

Building SQL queries by concatenating user input. Always use prepared statements with placeholders.

**Bad:**

```go
query := fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", input)
query := "SELECT * FROM users WHERE id = " + id
query := "DELETE FROM orders WHERE id = " + strconv.Itoa(orderID) // safe but inconsistent — use placeholders everywhere
```

**Good:**

```go
// Placeholder syntax varies by driver: $1 (pgx/lib/pq), ? (MySQL/SQLite)
db.QueryRow("SELECT * FROM users WHERE name = $1", input)
db.Exec("DELETE FROM orders WHERE id = $1", orderID)
```

### Dynamic IN clauses

Never build `IN (...)` by joining user strings. Generate numbered placeholders.

**Bad:**

```go
query := fmt.Sprintf("SELECT * FROM users WHERE id IN (%s)", strings.Join(ids, ","))
```

**Good:**

```go
// Build placeholders: $1, $2, $3, ...
placeholders := make([]string, len(ids))
args := make([]any, len(ids))
for i, id := range ids {
    placeholders[i] = fmt.Sprintf("$%d", i+1)
    args[i] = id
}
query := fmt.Sprintf("SELECT * FROM users WHERE id IN (%s)", strings.Join(placeholders, ","))
rows, err := db.Query(query, args...)
```

With `sqlx`:

```go
query, args, err := sqlx.In("SELECT * FROM users WHERE id IN (?)", ids)
query = db.Rebind(query) // converts ? to $1,$2,... for postgres
rows, err := db.Query(query, args...)
```

### Dynamic column names and ORDER BY

Placeholders only work for **values**, not identifiers (table/column names) or SQL keywords. Allowlist identifiers explicitly.

**Bad:**

```go
query := fmt.Sprintf("SELECT * FROM users ORDER BY %s", sortCol) // SQL injection
```

**Good:**

```go
allowed := map[string]string{
    "name": "name", "created": "created_at", "email": "email",
}
col, ok := allowed[sortCol]
if !ok {
    col = "created_at"
}
query := fmt.Sprintf("SELECT * FROM users ORDER BY %s", col) // safe: col is from allowlist
```

### Dynamic WHERE filters

Build queries incrementally; parameterize every user-supplied value.

```go
var conditions []string
var args []any
idx := 1

if name != "" {
    conditions = append(conditions, fmt.Sprintf("name = $%d", idx))
    args = append(args, name)
    idx++
}
if minAge > 0 {
    conditions = append(conditions, fmt.Sprintf("age >= $%d", idx))
    args = append(args, minAge)
    idx++
}

query := "SELECT * FROM users"
if len(conditions) > 0 {
    query += " WHERE " + strings.Join(conditions, " AND ")
}
rows, err := db.Query(query, args...)
```

### Prefer `sqlx` or `pgx` over raw `database/sql`

Libraries like `sqlx` and `pgx` provide safer ergonomics (named parameters, `IN` clause expansion, struct scanning) while still using prepared statements under the hood. They reduce the temptation to fall back to string concatenation for complex queries.

---

## XPath Injection — High

XPath injection allows manipulation of XML data queries.

**Bad:**

```go
xpathQuery := "//user[@username='" + username + "']" // Vulnerable
```

**Good:**

```go
// Use numeric ID
xpathQuery := fmt.Sprintf("//user[@id='%d']", userID)

// Or parse XML without XPath
```

---

## Code Injection — Critical

Generating code from unvalidated user input.

**Bad:**

```go
template := "func handle" + resourceName + "() {...}" // DON'T
```

**Good:**

```go
// Validate resource name matches whitelist
if !allowedResources[resourceName] {
    return errors.New("invalid resource")
}
// Use predefined templates
```

---

## Command Injection — Critical

Passing unvalidated input to shell commands.

**Bad:**

```go
cmd := exec.Command("sh", "-c", "rm -f /tmp/"+filename) // DON'T
```

**Good:**

```go
// Validate the filename BEFORE building or running the command
if filepath.Base(filename) != filename {
    return errors.New("invalid filename")
}
cmd := exec.Command("rm", "-f", filepath.Join("/tmp", filename))
```

---

## Template Injection — High

Using untrusted input in templates.

**Bad:**

```go
tmplText := r.URL.Query().Get("tpl") // Untrusted input becomes template source
t := template.Must(template.New("t").Parse(tmplText)) // DON'T: SSTI
t.Execute(w, nil)
```

**Good:**

```go
// Parse a constant template; pass user data only to Execute.
var t = template.Must(template.New("t").Parse("<div>{{.}}</div>"))

func handler(w http.ResponseWriter, r *http.Request) {
    user := strings.TrimSpace(r.URL.Query().Get("user"))
    t.Execute(w, user)
}
```

---

## Cross-Site Scripting (XSS) — High

XSS allows attackers to execute malicious scripts.

**Bad:**

```go
w.Write([]byte(fmt.Sprintf("<div>%s</div>", data))) // DON'T
```

**Good:**

```go
import "html/template"
t := template.Must(template.New("safe").Parse("<div>{{.}}</div>"))
t.Execute(w, data) // Auto-escapes
```

---

## HTML Tag Injection — High

Injecting HTML tags through unvalidated input.

**Bad:**

```go
fmt.Fprintf(w, "<div>Welcome, %s!</div>", input) // DON'T
```

**Good:**

```go
import "html"
escaped := html.EscapeString(input)
fmt.Fprintf(w, "<div>Welcome, %s!</div>", escaped)
```

---

## Server-Side Request Forgery (SSRF) — High

Forcing the server to make requests to unintended endpoints.

**Bad:**

```go
url := r.URL.Query().Get("url")
resp, _ := http.Get(url) // DON'T: No validation
```

**Good:**

```go
u, err := url.Parse(targetURL)
if err != nil {
    return err
}
// Block non-HTTP/S protocols
if u.Scheme != "http" && u.Scheme != "https" {
    return errors.New("invalid scheme")
}
// Allowlist hosts (preferred over denylists)
if !allowedHosts[u.Hostname()] {
    return errors.New("host not allowed")
}

// Check IPs at dial time (defeats DNS rebinding) and on every redirect.
dialer := &net.Dialer{
    Timeout: 5 * time.Second,
    Control: func(network, address string, _ syscall.RawConn) error {
        host, _, err := net.SplitHostPort(address)
        if err != nil {
            return err
        }
        ip, err := netip.ParseAddr(host)
        if err != nil {
            return err
        }
        ip = ip.Unmap()
        if ip.IsLoopback() || ip.IsPrivate() || ip.IsLinkLocalUnicast() ||
            ip.IsLinkLocalMulticast() || ip.IsUnspecified() {
            return errors.New("blocked address") // also covers link-local cloud metadata IPs
        }
        return nil
    },
}
client := &http.Client{
    Transport: &http.Transport{DialContext: dialer.DialContext},
    CheckRedirect: func(req *http.Request, via []*http.Request) error {
        if len(via) >= 3 || !allowedHosts[req.URL.Hostname()] {
            return errors.New("redirect not allowed")
        }
        return nil
    },
}
resp, err := client.Get(u.String())
```

---

## Unsafe Deserialization — Critical

Deserializing untrusted input can exhaust resources or bypass validation (gob and encoding/json do not execute code; unsafe deserializers in other ecosystems can).

**Bad:**

```go
dec := gob.NewDecoder(r.Body) // DON'T: unbounded gob input can exhaust memory/CPU
var user interface{}
dec.Decode(&user)
```

**Good:**

```go
import "encoding/json"
r.Body = http.MaxBytesReader(w, r.Body, 1<<20) // bound input size
dec := json.NewDecoder(r.Body)
var user User // decode into a concrete type
dec.Decode(&user)
// Validate fields
// gob is fine for trusted peers; for untrusted input bound its size with
// MaxBytesReader and decode into concrete types only.
```

---

## CWE References

- **CWE-78**: OS Command Injection
- **CWE-89**: SQL Injection
- **CWE-94**: Code Injection
- **CWE-79**: Cross-site Scripting (XSS)
- **CWE-918**: Server-Side Request Forgery (SSRF)
- **CWE-502**: Deserialization of Untrusted Data
- **CWE-20**: Improper Input Validation
