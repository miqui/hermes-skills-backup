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

Go-side workflow for an **OpenAPI 3.2.0** contract: author the document spec-first, load/validate it from Go, serve it, and check or generate code against it. The document itself (syntax, `$self`, tags, `QUERY`, `itemSchema`, migration) belongs to `openapi-specification`; follow it and do not restate it here. This skill covers only the Go tooling around it.

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

## 2. Tool-support matrix (checked against primary sources, Oct 2026)

| Tool | 3.2 status | Source |
| --- | --- | --- |
| `pb33f/libopenapi` | **Supported.** README: "full support for OpenAPI 3, 3.1 and 3.2"; also Overlays, Arazzo | libopenapi README |
| `pb33f/libopenapi-validator` | **Supported** for document validation ("explicitly covered for 3.0, 3.1, and 3.2"); also validates `*http.Request` / `*http.Response` | validator README (pkg.go.dev v0.16.1) |
| `getkin/kin-openapi` | **Partial, in progress.** v0.151.0 "recognize OpenAPI 3.2.1", `additionalOperations` key checks; built-in schema validator file is still named `schema_3point0_validator.go`. Do not assume full 3.2 semantics | kin-openapi releases; oapi-codegen #2436 |
| `oapi-codegen` | **No 3.2 yet.** README claims 3.0 and 3.1. Issue #2436 (open): maintainer waits on a kin-openapi release, then plans `QUERY`/custom methods. The same thread says kin-openapi's 3.1 isn't complete, so treat README "3.1" as best-effort | README; #2436 |
| `ogen` | **No 3.2.** Issue #1610 open; maintainer plans to migrate to libopenapi + schemacompiler and support 3.2 | #1610 |
| `huma` | **3.1 only** ("Described by OpenAPI 3.1"); 3.2 is only a discussion (#900) | README; #900 |
| `swag` v1 (v1.16.x) | **Swagger 2.0 output only** | swag README |
| `swag` v2 (v2.0.0-rc6, release candidate) | opt-in OpenAPI **3.1**; README still says "Swagger 2.0"; **not 3.2** | swag releases, pkg.go.dev |
| Redoc | Redoc 2 rejects 3.2.0 (issue #2773). Redoc CE 3 claims 3.2, but per Redocly's own blog npm still ships `3.0.0-rc.0` (older engine), so not installable yet | Redocly blog, issue |
| Scalar | Vendor docs claim 3.2 (nested tags, whole-query params); **not tested here** | scalar.com |
| Swagger UI | "basic support since 5.32.0" is secondhand (Scalar comparison page): **unverified**. UI version inside `swaggo/files`: **unverified** | n/a |

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
    doc, err := libopenapi.NewDocument(b) // documented
    if err != nil {
        return err
    }
    if _, err := doc.BuildV3Model(); err != nil { // documented; v3 model covers 3.x
        return err
    }
    v, errs := validator.NewValidator(doc) // documented
    if len(errs) > 0 {
        return errs[0]
    }
    ok, verrs := v.ValidateDocument() // method name: UNVERIFIED, confirm with `go doc`
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
- Spec with relative `$ref` files: `libopenapi.NewDocumentWithConfiguration(b, &datamodel.DocumentConfiguration{AllowFileReferences: true, BasePath: dir})` (documented).
- `ValidateHttpRequest(*http.Request)` on the validator is documented; use it in contract tests or middleware.
- pb33f APIs shift between minors: pin versions and confirm signatures with `go doc`.

## 4. Embed and serve the spec

```go
//go:embed openapi.yaml
var spec []byte // openapi.yaml sits next to this file

func specHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/yaml")
    w.Write(spec)
}

mux.HandleFunc("GET /openapi.yaml", specHandler) // Go 1.22+ patterns
```

- Embed one canonical file (bundle `$ref`s first, or use `embed.FS`).
- Keep `$self` and `servers` in the spec, not patched in Go code.
- Gate the spec and any docs UI per environment (`golang-security`).
- Point a UI at `/openapi.yaml` (Scalar via its CDN script with `data-url`, or a recent self-hosted Swagger UI; both snippet shapes unverified here). Render a 3.2-only construct (`QUERY`, `itemSchema`, nested tags) before trusting the UI.

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
    echoSwagger "github.com/swaggo/echo-swagger"
    fiberSwagger "github.com/swaggo/fiber-swagger"
    httpSwagger "github.com/swaggo/http-swagger/v2"
)

r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler)) // Gin
e.GET("/swagger/*", echoSwagger.WrapHandler)                         // Echo; a V3 variant (WrapHandlerV3) exists in echo-swagger v2: UNVERIFIED
app.Get("/swagger/*", fiberSwagger.WrapHandler)                      // Fiber
// net/http and chi: httpSwagger.Handler takes options, NOT swaggerFiles.Handler
mux.Handle("/swagger/", httpSwagger.WrapHandler)                     // net/http
r.Get("/swagger/*", httpSwagger.Handler(httpSwagger.URL("/swagger/doc.json"))) // chi
```

UI path: `/swagger/index.html`. These UIs render whatever swag emitted (2.0/3.1); they do not make it 3.2.
