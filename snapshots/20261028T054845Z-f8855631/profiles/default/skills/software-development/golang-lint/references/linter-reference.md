# Linter Reference

golangci-lint v2 uses a `.golangci.yml` with `version: "2"` at the project root.

Key sections of `.golangci.yml`:

- **`run`** — concurrency, timeout, test inclusion
- **`linters.enable`** / **`linters.disable`** — which linters are active
- **`linters.settings`** — per-linter thresholds and options
- **`formatters`** — code formatters (gofmt, gofumpt)
- **`linters.exclusions`** — path/generated-code exclusions (also `formatters.exclusions`)
- **`issues`** — output limits, exclusion rules

To add a linter: add it to `linters.enable` and optionally configure it in `linters.settings`.

To disable a linter: move it to `linters.disable` with a comment explaining why.

## Linter Categories

The recommended configuration enables linters across these domains:

| Domain | Linters | Catches |
| --- | --- | --- |
| Correctness | govet, staticcheck, unused, errcheck, nilerr, forcetypeassert, copyloopvar, errorlint, durationcheck, reassign | Bugs, unchecked errors, stdlib misuse |
| Style | gocritic, revive, wsl_v5, whitespace, godot, misspell, predeclared, errname, dupword, asciicheck | Readability, naming, consistency |
| Complexity | gocyclo, nestif, funlen, dupl | Overly complex or duplicated code |
| Performance | perfsprint, unconvert, ineffassign, goconst | Conversions, string ops, dead assigns |
| Security & resources | gosec, bidichk, bodyclose, noctx, sqlclosecheck, rowserrcheck, containedctx, fatcontext | Insecure code, resource leaks (HTTP, SQL), context misuse |
| Logging | sloglint, loggercheck | Consistent slog usage, key/value pair validation |
| Testing | thelper, paralleltest, testifylint, usetesting | Test hygiene and best practices |
| Modernization | modernize, exptostd, intrange, usestdlibvars, exhaustive, nolintlint | Modern Go idioms, lint hygiene |
| Formatting | gofmt, gofumpt | Code formatting |

The bundled [recommended .golangci.yml](../assets/.golangci.yml) enables a broad set of linters across these domains, organized as a practical default rather than an exhaustive policy for every repo.

### Correctness & Safety

- **govet** — Go's built-in checker: copylocks, printf format mismatches, struct tag validation, unreachable code, and other `go vet` analyzers
- **staticcheck** — Extensive static analysis: deprecated APIs, common mistakes, unnecessary code, simplifications, misuse of standard library
- **unused** — Detects unused variables, functions, types, and struct fields
- **errcheck** — Ensures all error returns are checked, including type assertions (configured with `check-type-assertions: true`)
- **nilerr** — Detects returning nil error when `err` is non-nil (common source of silent failures)
- **forcetypeassert** — Flags type assertions without the comma-ok check (`v := x.(T)` instead of `v, ok := x.(T)`)
- **copyloopvar** — Detects loop variable copy issues (Go 1.22+)
- **errorlint** — Enforces `errors.Is`/`errors.As` and `%w` wrapping over comparisons and type assertions on errors
- **durationcheck** — Detects suspicious multiplication of two `time.Duration` values
- **reassign** — Flags reassignment of package-level variables from other packages

### Style & Readability

- **gocritic** — Opinionated style checks: unnecessary conversions, range copies, append-assign patterns, redundant code
- **revive** — Naming conventions for exported types, unexported returns, receiver naming, error naming, stuttered package names
- **wsl_v5** — Whitespace and blank line rules for visual grouping and readability
- **whitespace** — Detects trailing whitespace and unnecessary blank lines in function bodies
- **godot** — Ensures exported-symbol comments end with a period
- **misspell** — Catches common English misspellings in identifiers and comments
- **predeclared** — Flags shadowing of Go built-in identifiers (e.g., naming a variable `len`, `cap`, `error`)
- **errname** — Enforces error naming conventions: error types suffixed with `Error` (e.g., `DecodeError`), error variables prefixed with `Err` (e.g., `ErrNotFound`)
- **dupword** — Finds duplicated words in comments and strings ("the the")
- **asciicheck** — Flags non-ASCII identifiers

### Complexity

- **gocyclo** — Cyclomatic complexity threshold (configured: 13). Functions exceeding this should be split
- **nestif** — Detects deeply nested if/else chains that harm readability
- **funlen** — Function length limits (configured: 120 lines, 80 statements)
- **dupl** — Code duplication detection (configured: threshold 100 tokens)

### Performance

- **perfsprint** — Suggests faster alternatives to `fmt.Sprintf` (e.g., `strconv.Itoa` instead of `fmt.Sprintf("%d", n)`)
- **unconvert** — Detects unnecessary type conversions (e.g., `int(x)` when `x` is already `int`)
- **ineffassign** — Detects assignments to variables that are never subsequently read
- **goconst** — Detects repeated string/number literals that should be extracted to constants (configured: min length 3, min 4 occurrences)

### Security & Resources

- **bodyclose** — Ensures HTTP response bodies are closed (unclosed bodies leak connections)
- **sqlclosecheck** — Ensures `sql.Rows` and `sql.Stmt` are closed after use
- **rowserrcheck** — Ensures `sql.Rows.Err()` is checked after iteration
- **gosec** — Security scanner: SQL injection, hardcoded credentials, weak crypto, path traversal
- **noctx** — HTTP requests made without a `context.Context`
- **containedctx** — Flags `context.Context` stored in struct fields
- **fatcontext** — Detects context nesting in loops/closures that grows without bound

### Logging

- **sloglint** — Enforces consistent `log/slog` usage (key/value pairs, no mixing of styles)
- **loggercheck** — Validates key/value argument pairs for slog/logr/zap loggers

### Testing

- **thelper** — Ensures test helpers call `t.Helper()` so failures report the correct call site
- **paralleltest** — Detects tests and subtests missing `t.Parallel()` calls
- **testifylint** — Enforces testify best practices (e.g., `assert.Equal(t, expected, actual)` over `assert.True(t, expected == actual)`)
- **usetesting** — Prefers `t.TempDir()`, `t.Setenv()`, `t.Context()` etc. over `os`/`context` equivalents in tests

### Modernization & Meta

- **exptostd** — Replaces `golang.org/x/exp` functions with standard-library equivalents
- **modernize** — Detects code that can be rewritten using newer Go features (needs a golangci-lint release that includes it; check `golangci-lint linters`)
- **intrange** — Suggests `range N` over C-style `for i := 0; i < N; i++` loops (Go 1.22+)
- **usestdlibvars** — Replaces hardcoded strings/numbers with stdlib constants (e.g., `http.MethodGet` instead of `"GET"`)
- **exhaustive** — Ensures switch statements on enum types cover all possible values
- **nolintlint** — Enforces proper `//nolint` directive usage: requires linter name and justification comment (configured with `require-explanation` and `require-specific`)

### Disabled by default

See the comments in `linters.disable` of the [recommended .golangci.yml](../assets/.golangci.yml) for each disabled linter and its rationale (e.g. `exhaustruct_v5` fights Go's zero-value idiom).

### Formatting

Formatters run via `golangci-lint fmt ./...`:

- **gofmt** — Standard Go formatter (canonical formatting)
- **gofumpt** — Stricter formatter with extra rules (configured with `extra-rules: true`): consistent empty lines, grouped imports, simplified code patterns
