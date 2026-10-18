# Filesystem Security Rules

Filesystem vulnerabilities can lead to unauthorized file access, data leakage, and denial-of-service attacks.

**Rules:**

1. File paths MUST be sanitized against traversal (`../`).
2. `os.Root` SHOULD be used for scoped file access (Go 1.24+).
3. Zip extraction MUST check for ZipSlip path traversal.
4. Temporary files MUST use `os.CreateTemp` — NEVER predictable names.
5. File permissions MUST be restrictive (0600 for secrets, 0750 for directories).

---

## Directory Traversal — High

Paths like `../../etc/passwd` access files outside intended directory.

**Bad:**

```go
filepath := filepath.Join("/var/www", filename) // DON'T
http.ServeFile(w, r, filepath)
```

**Good (Go 1.24+) — use `os.Root` for safe, scoped directory access:**

```go
root, err := os.OpenRoot("/var/www")
if err != nil { return err }
defer root.Close()
f, err := root.Open(filename) // cannot escape root directory
```

`os.Root` prevents path traversal at the OS level — no manual path validation needed for containment. All operations (`Open`, `Create`, `Stat`, `OpenFile`, etc.) are confined to the root directory. Symlinks that resolve outside the root are rejected. `Root.FS` is Go 1.24. Go 1.25 added `Chmod, Chown, Chtimes, Lchown, Link, MkdirAll, ReadFile, Readlink, RemoveAll, Rename, Symlink, WriteFile`.

Caveats: `Root` follows symlinks that stay inside the root; it does not defend against hard links, bind mounts, or Windows reserved names.

**Good (pre-Go 1.24 fallback):**

```go
fullPath := filepath.Join(baseDir, filename)
rel, err := filepath.Rel(filepath.Clean(baseDir), fullPath)
if err != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
    return errors.New("access denied")
}
// Note: a bare strings.HasPrefix(fullPath, baseDir) also matches "/var/www-evil".
// Neither check resolves symlinks; prefer os.Root.
```

---

## Zip Archive Path Traversal — High

Malicious zip files can escape extraction directory.

**Bad:**

```go
for _, file := range reader.File {
    path := filepath.Join(dest, file.Name) // DON'T: No validation
    file.Create(path)
}
```

**Good (Go 1.24+) — use `os.Root` to scope extraction:**

```go
root, err := os.OpenRoot(dest)
if err != nil { return err }
defer root.Close()
const maxTotal = 100 << 20 // cap total extracted bytes
var total int64
for _, file := range reader.File {
    if file.FileInfo().IsDir() {
        continue
    }
    if err := root.MkdirAll(filepath.Dir(file.Name), 0o750); err != nil {
        return err // rejects paths escaping root
    }
    out, err := root.OpenFile(file.Name, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
    if err != nil { return err }
    rc, err := file.Open()
    if err != nil { out.Close(); return err }
    n, err := io.Copy(out, io.LimitReader(rc, maxTotal-total+1))
    rc.Close()
    out.Close()
    total += n
    if err != nil { return err }
    if total > maxTotal { return errors.New("archive too large") }
}
```

**Good (pre-Go 1.24 fallback):**

```go
for _, file := range reader.File {
    if strings.Contains(file.Name, "..") || strings.HasPrefix(file.Name, "/") {
        return errors.New("invalid path")
    }
    targetPath := filepath.Join(dest, file.Name)
    if !strings.HasPrefix(filepath.Clean(targetPath), filepath.Clean(dest)+string(filepath.Separator)) {
        return errors.New("path traversal attempt")
    }
}
```

---

## Decompression Bomb — Medium

Tiny compressed files can expand to GBs.

**Bad:**

```go
gr, _ := gzip.NewReader(f)
out, _ := os.Create(dst)
io.Copy(out, gr) // DON'T: No size limits
```

**Good:**

```go
const maxDecompressedSize = 100 * 1024 * 1024 // 100MB limit

type limitedReader struct {
    r    io.Reader
    read int64
}

// Returns an error (not a silent EOF) when the limit is exceeded, so data is never truncated unnoticed.
func (l *limitedReader) Read(p []byte) (int, error) {
    if l.read > maxDecompressedSize {
        return 0, errors.New("decompressed data exceeds limit")
    }
    // read at most one byte past the limit so over-limit input is detected
    if rem := maxDecompressedSize + 1 - l.read; int64(len(p)) > rem {
        p = p[:rem]
    }
    n, err := l.r.Read(p)
    l.read += int64(n)
    if l.read > maxDecompressedSize {
        return n, errors.New("decompressed data exceeds limit")
    }
    return n, err
}

lr := &limitedReader{r: gr}
if _, err := io.Copy(out, lr); err != nil {
    return err
}
```

---

## Insecure Temporary File Creation — Medium

Creating temp files without proper permissions.

**Bad:**

```go
f, _ := os.Create("/tmp/myapp.temp") // DON'T: Predictable name
f.WriteString(data)
```

**Good:**

```go
f, err := os.CreateTemp("", "myapp.*") // already created with mode 0600
if err != nil { return err }
defer os.Remove(f.Name())
defer f.Close()
```

---

## Insecure File Permissions — Medium

Opening files with excessive permissions.

**Bad:**

```go
f, _ := os.OpenFile("config.json", os.O_CREATE, 0644) // DON'T: World-readable
```

**Good:**

```go
f, _ := os.OpenFile("config.json", os.O_CREATE, 0600) // OK: Owner only
```

---

## Insecure mkdir — Low

Creating directories with overly permissive permissions.

**Bad:**

```go
os.MkdirAll("/var/myapp/cache", 0777) // DON'T: World-writable
```

**Good:**

```go
os.MkdirAll("/var/myapp/cache", 0750) // OK: owner rwx, group r-x
```

---

## Insecure File Write Permissions — Medium

Opening files for writing with inappropriate permissions.

**Bad:**

```go
os.OpenFile("app.log", os.O_CREATE, 0666) // DON'T: World-writable
```

**Good:**

```go
os.OpenFile("app.log", os.O_CREATE|os.O_APPEND, 0640) // OK
```

---

## Tainted File Read — High

Reading files based on unvalidated input.

**Bad:**

```go
func readFile(filename string) ([]byte, error) {
    return os.ReadFile(filename) // DON'T: No validation
}
```

**Good (Go 1.24+):**

```go
const allowedDir = "/var/www/public/"

func readFile(filename string) ([]byte, error) {
    root, err := os.OpenRoot(allowedDir)
    if err != nil { return nil, err }
    defer root.Close()
    f, err := root.Open(filename) // cannot escape root directory
    if err != nil { return nil, err }
    defer f.Close()
    return io.ReadAll(f)
}
```

**Good (pre-Go 1.24 fallback):**

```go
const allowedDir = "/var/www/public/"

func readFile(filename string) ([]byte, error) {
    if strings.Contains(filename, "..") {
        return nil, errors.New("invalid filename")
    }
    fullPath := filepath.Join(allowedDir, filename)
    if !strings.HasPrefix(filepath.Clean(fullPath), filepath.Clean(allowedDir)+string(filepath.Separator)) {
        return nil, errors.New("access denied")
    }
    return os.ReadFile(fullPath)
}
```

---

## CWE References

- **CWE-22**: Path Traversal (Directory Traversal)
- **CWE-409**: Zip Bomb Decompression
- **CWE-379**: Insecure Temp File Creation
- **CWE-732**: Incorrect File Permissions
