---
name: golang-openapi
description: "Use when building, serving, validating, or generating Go code from OpenAPI 3.2 contracts. Spec-first Go workflow with a verified tool-support matrix (libopenapi, kin-openapi, oapi-codegen, ogen, huma), go:embed spec serving, and a labelled legacy appendix for swaggo/swag (Swagger 2.0 / 3.1 RC) and Swagger UI wiring."
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [golang, go, openapi, openapi-3-2, spec-first, libopenapi, oapi-codegen, api-contract, swaggo-legacy]
    related_skills: [openapi-specification, openapi-api-designer, api-governance, golang-security, go-builder, golang-testing, golang-lint]
---

# Go + OpenAPI 3.2

## Overview

Go-side workflow for an **OpenAPI 3.2.0** contract: author the document spec-first, load/validate it from Go, serve it, and check or generate code against it. The document itself (syntax, `$self`, nested tags with `parent`/`kind`, the `query` Path Item field and `additionalOperations`, `itemSchema`, migration) belongs to `openapi-specification`; follow it and do not restate it here. This skill covers only the Go tooling around it.

Hard rule: the contract declares `openapi: 3.2.0`. Annotation generators that emit older versions (swag, see Legacy Appendix) are not a path to 3.2. Never relabel their output as 3.2.0.

## When to Use

- Starting or maintaining a Go service whose contract is OpenAPI 3.2
- Choosing a Go library or generator and needing to know what really supports 3.2
- Loading, validating, or diffing a 3.2 document in Go code or CI
- Embedding and serving the spec and a docs UI from a Go binary
- Maintaining existing swaggo/swag code (Legacy Appendix)

Not for: authoring spec content (`openapi-specification`), API design (`openapi-api-designer`), governance gates (`api-governance`), gRPC-only services.

## 1. Spec-first workflow

1. Write `api/openapi.yaml` (`openapi: 3.2.0`) per `openapi-specification`; lint it in CI.
2. Validate it with a 3.2-aware tool (section 3).
3. Implement handlers; check them against the contract in tests (`golang-testing`).
4. Embed the spec in the binary and serve it (section 4).
5. Diff the spec on every PR for breaking changes (`api-governance`).

Prefer spec-first: no mainstream Go annotation generator emits 3.2 (matrix below).

## 2. Tool-support matrix

Verified 2026-10-18 from primary pages (GitHub issues/releases/READMEs) only where a row says "verified"; anything marked *unverified* or "not re-checked" was not re-fetched that day. Re-check before committing; this moves fast.

| Tool | 3.2 status | Source |
| --- | --- | --- |
| `pb33f/libopenapi` | **Supported.** README: "full support for OpenAPI 3, 3.1 and 3.2"; also Overlays, Arazzo | libopenapi README; verified by running 2026-10-18 with libopenapi@v0.41.6: a 3.2.0 doc using `$self`, `query`, `additionalOperations`, tag `summary`/`parent`/`kind` and `itemSchema` (`application/jsonl`) loads with `NewDocument` + `BuildV3Model` (no errors); the model exposes `PathItem.Query`, `.AdditionalOperations`, `Model.Self`, `Tag.Parent/Kind/Summary` |
| `pb33f/libopenapi-validator` | **Supported** for document validation ("explicitly covered for 3.0, 3.1, and 3.2"); also validates `*http.Request` / `*http.Response` | validator README; verified by running 2026-10-18 with libopenapi-validator@v0.16.1 + libopenapi@v0.41.6: the same 3.2.0 doc passes `ValidateDocument()`; a doc with an unknown path-item field and a response missing `description` is rejected ("not valid according to the 3.2.0 specification") |
| `getkin/kin-openapi` | **Partial, in progress.** Issue #1212 "Support for OpenAPI 3.2" closed as completed 2026-08-05, fixed by PR #1240 (custom methods). Verified by running 2026-10-18: `openapi3.PathItem.Query` first compiles at kin-openapi v0.147.0 (absent in v0.142.0 and v0.143-v0.146). With v0.151.0, `LoadFromData` accepts a 3.2.0 doc with `query` and `additionalOperations` (`Operations()` returns GET, QUERY, COPY), but `Validate()` rejects top-level `$self` ("extra sibling fields: [$self]") and tag `kind`/`summary` ("extra sibling fields: [kind summary]"). `itemSchema` and tag `parent` were not isolated. Use libopenapi-validator for 3.2 validation; do not assume full 3.2 semantics | kin-openapi #1212, #1240 (verified 2026-10-18) |
| `oapi-codegen` | **No 3.2 yet.** README 3.0/3.1 claim not re-checked. Issue #2436 (open, last update 2026-09-18): maintainer will add 3.2 after kin-openapi releases the custom-methods change; routers need custom-method setup (Chi, Fiber) for `query`; thread says kin-openapi's 3.1 was incomplete | #2436 (verified 2026-10-18) |
| `ogen` | **No 3.2.** Issue #1610 open (last update 2026-07-23); maintainer: "planning to migrate to libopenapi and schemacompiler and support v3.2" | #1610 (verified 2026-10-18) |
| `huma` | **3.1 only** (README claim not re-checked); 3.2 is only discussion #900 (Oct 2025: maintainers interested, no timeframe, PRs welcome) | #900 (verified 2026-10-18) |
| `swag` v1 (v1.16.x) | **Swagger 2.0 output only** (not re-checked 2026-10-18) | swag README |
| `swag` v2 (v2.0.0-rc6, release candidate) | opt-in OpenAPI **3.1**; README still says "Swagger 2.0"; **not 3.2** (not re-checked 2026-10-18) | swag releases, pkg.go.dev |
| Redoc | Redoc rejects 3.2.0: "Unsupported OpenAPI version: 3.2.0" (issue #2773, verified 2026-10-18); Redocly CLI has begun incremental 3.2 support. Redoc CE 3 / npm state: **unverified** (secondhand, Redocly blog) | redoc #2773 |
| Scalar | `@scalar/openapi-parser` README: "support for OpenAPI 3.2, 3.1, 3.0 and Swagger 2.0" (verified 2026-10-18; parser only). Docs-UI rendering of 3.2 constructs **not tested here** | scalar repo |
| Swagger UI | v5.32.0 (2026-02-27): "oas32: add basic OpenAPI 3.2.0 support"; v5.32.15 (2026-09-04) fixed `query` in default `supportedSubmitMethods`; latest seen v5.33.1 (2026-10-01). "Basic": test with your spec. UI version bundled in `swaggo/files`: **unverified** | swagger-ui releases (verified 2026-10-18) |

Re-check before committing to a tool; this moves fast.

## 3. Load and validate a 3.2 document (libopenapi)

```go
import (
    "fmt"
    "os"

    "github.com/pb33f/libopenapi"
    validator "github.com/pb33f/libopenapi-validator"
)

func CheckSpec(path string) error {
    b, err := os.ReadFile(path)
    if err != nil {
        return err
    }
    doc, err := libopenapi.NewDocument(b) // run on a 3.2.0 doc, libopenapi@v0.41.6
    if err != nil {
        return err
    }
    if _, err := doc.BuildV3Model(); err != nil { // v3 model covers 3.2 (run 2026-10-18)
        return err
    }
    v, errs := validator.NewValidator(doc) // (Validator, []error), libopenapi-validator@v0.16.1
    if len(errs) > 0 {
        return errs[0]
    }
    ok, verrs := v.ValidateDocument() // (bool, []*errors.ValidationError); run 2026-10-18
    if !ok {
        for _, e := range verrs {
            fmt.Println(e.Message, "|", e.HowToFix)
        }
        return fmt.Errorf("invalid OpenAPI document")
    }
    return nil
}
```

- Use as a test/CI helper, not request-path code.
- Spec with relative `$ref` files: `libopenapi.NewDocumentWithConfiguration(b, &datamodel.DocumentConfiguration{AllowFileReferences: true, BasePath: dir})` (documented; add import `github.com/pb33f/libopenapi/datamodel`).
- `ValidateHttpRequest(*http.Request)` on the validator is documented; use it in contract tests or middleware.
- pb33f APIs shift between minors: pin versions and confirm signatures with `go doc`.

## 4. Embed and serve the spec

```go
import (
    _ "embed" // required for go:embed into a []byte
    "net/http"
)

//go:embed openapi.yaml
var spec []byte // openapi.yaml sits next to this file

func specHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/yaml")
    _, _ = w.Write(spec)
}

func routes() *http.ServeMux {
    mux := http.NewServeMux()
    mux.HandleFunc("GET /openapi.yaml", specHandler) // Go 1.22+ patterns
    return mux
}
```

- Embed one canonical file (bundle `$ref`s first, or use `embed.FS`).
- Keep `$self` and `servers` in the spec, not patched in Go code.
- Gate the spec and any docs UI per environment (`golang-security`).
- Point a UI at `/openapi.yaml` (Scalar via its CDN script with `data-url`, or a recent self-hosted Swagger UI; both snippet shapes unverified here). Render a 3.2-only construct (a `query` operation, `itemSchema`, nested tags) before trusting the UI.

## 5. Code generation and server choices

- Need 3.2 constructs in generated code: no mainstream generator handles them yet. Hand-write handlers and check them with libopenapi-validator in tests, or generate from a down-levelled 3.1 copy and record what was lost.
- oapi-codegen / ogen: 3.0/3.1 input only today; re-check #2436 / #1610.
- huma: emits 3.1; do not claim 3.2 for it.
- Never bump `openapi:` to `3.2.0` without migrating constructs (`openapi-specification`).

## 6. Cross-references

- `openapi-specification`: 3.2 syntax, validation, migration (authoritative for the contract)
- `openapi-api-designer`: resource/capability design before writing the spec
- `api-governance`: lifecycle, breaking-change review, publication gates
- `golang-security`: hardening and gating spec/docs endpoints
- `go-builder`: service layout and build setup
- `golang-testing`: contract tests against the spec
- `golang-lint`: lint config for generated/embedded code

## 7. Common Mistakes

| Mistake | Fix |
| --- | --- |
| Relabelling swag output as `3.2.0` | Never. swag emits 2.0 (v1) or 3.1 (v2 rc). Migrate per `openapi-specification` |
| Assuming "supports OpenAPI 3.x" includes 3.2 | Check the matrix; most tools stop at 3.0/3.1 |
| Server URLs/`$self` set in Go code, drifting from the spec | Keep them in the spec |
| Validating only at runtime | Validate in CI with libopenapi |
| Trusting vendor "3.2 support" claims | Render your own spec first |

## 8. Verification Checklist

- [ ] Served/embedded document declares `openapi: 3.2.0`
- [ ] Document validates with libopenapi(-validator) in CI
- [ ] The generator/server version you use is confirmed for the OpenAPI version you actually feed it
- [ ] `GET /openapi.yaml` returns the embedded bytes
- [ ] Docs UI renders a 3.2-only construct from your spec, or the fallback is deliberate
- [ ] Spec and docs endpoints are gated per environment
- [ ] No swag output is published as 3.2

## 9. Legacy Appendix: swaggo/swag

> **swag v1 (v1.16.x) emits Swagger 2.0. swag v2 (v2.0.0-rc6, release candidate) has opt-in OpenAPI 3.1 output. Neither emits 3.2.** Never relabel the `swagger`/`openapi` field to `3.2.0`. Use this only to maintain existing swag code or as migration input.

- Annotations, security definitions, struct tags, common mistakes: [references/swag-legacy.md](./references/swag-legacy.md)
- CLI, generics, dynamic config, MIME aliases: [references/swag-cli.md](./references/swag-cli.md)
- `docs.SwaggerInfo.Host/BasePath/Schemes` are 2.0-only; in OAS 3.x they become `servers`.

Swagger UI wiring (blank-import the generated package: `import _ "yourmodule/docs"`):

```go
import (
    swaggerFiles "github.com/swaggo/files"
    ginSwagger "github.com/swaggo/gin-swagger"
    echoSwagger "github.com/swaggo/echo-swagger/v2" // Echo v5: github.com/labstack/echo/v5
    fiberSwagger "github.com/swaggo/fiber-swagger"
    httpSwagger "github.com/swaggo/http-swagger/v2"
)

r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler)) // Gin
e.GET("/swagger/*", echoSwagger.WrapHandler)                         // Echo v5 (Swagger 2.0 UI)
app.Get("/swagger/*", fiberSwagger.WrapHandler)                      // Fiber
// net/http and chi: httpSwagger.Handler takes options, NOT swaggerFiles.Handler
mux.Handle("/swagger/", httpSwagger.Handler(httpSwagger.URL("/swagger/doc.json"))) // net/http
r.Get("/swagger/*", httpSwagger.Handler(httpSwagger.URL("/swagger/doc.json"))) // chi
```

`echoSwagger.WrapHandlerV3` serves the OAS **3.0** doc (echo-swagger README, verified 2026-10-18); still not 3.2. The http-swagger and echo-swagger READMEs describe their output as Swagger 2.0. The wiring block above was compile-checked (`go vet`, 2026-10-18) against gin-swagger@v1.6.1, echo-swagger/v2@v2.0.1 + labstack/echo/v5@v5.4.0, fiber-swagger@v1.3.0 (+ gofiber/fiber/v2@v2.52.15), http-swagger/v2@v2.0.2, chi/v5@v5.5.0, swaggo/files@v1.0.1; not served or exercised.

UI path: `/swagger/index.html`. These UIs render whatever swag emitted (2.0/3.1); they do not make it 3.2.
