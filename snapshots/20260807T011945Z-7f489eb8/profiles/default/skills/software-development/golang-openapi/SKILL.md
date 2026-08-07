---
name: golang-openapi
description: "Use when adding, reviewing, or maintaining OpenAPI/Swagger documentation in a Go project, especially when using swaggo/swag annotations, generated docs, and framework-specific Swagger UI wiring."
version: 1.0.1
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [golang, go, openapi, swagger, swaggo, api-docs]
    related_skills: [openapi-specification, api-governance, golang-security, go-builder]
---

# Go OpenAPI / Swagger

## Overview

This skill covers OpenAPI documentation in Go projects that use `swaggo/swag`. It focuses on annotation structure, spec generation, framework wiring, security definitions, and the common mistakes that cause generated docs to drift from the actual API. For the generated contract itself, especially OpenAPI 3.2+ syntax, schema quality, validation, and migration questions, pair with `openapi-specification`.

Use this skill when the codebase already uses `swag`, when you are introducing Swagger UI to an HTTP service, or when you need to audit handler annotations for completeness and correctness.

## When to Use

- Adding Swagger/OpenAPI support to a Go HTTP service
- Reviewing handler annotations for correctness and completeness
- Wiring Swagger UI into Gin, Echo, Fiber, Chi, or `net/http`
- Fixing stale or incomplete generated OpenAPI docs
- Documenting request/response schemas, security requirements, and examples

Do not use this skill as the primary reference for broader API lifecycle governance or non-HTTP APIs like pure gRPC services.

## Setup

Typical setup steps:

```bash
swag init                        # generates docs/ with docs.go, swagger.json, swagger.yaml
swag init -g cmd/api/main.go     # if general info is not in main.go
swag fmt                         # format annotation comments
```

Import the generated `docs` package to register the spec. Use a blank import when only wiring the UI; use a named import when overriding `docs.SwaggerInfo` at runtime:

```go
import _ "yourmodule/docs"     // blank: registers spec
import docs "yourmodule/docs"  // named: override SwaggerInfo at runtime
```

Wire the UI endpoint for your framework:

```go
// Gin
r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

// Echo
e.GET("/swagger/*", echoSwagger.WrapHandler)

// Fiber
app.Get("/swagger/*", fiberSwagger.WrapHandler(swaggerFiles.Handler))

// net/http
mux.Handle("/swagger/", httpSwagger.Handler(swaggerFiles.Handler))

// Chi
r.Get("/swagger/*", httpSwagger.Handler(swaggerFiles.Handler))
```

Access the UI at `/swagger/index.html`.

For dynamic host or base path values, use a named import and override before serving:

```go
import docs "yourmodule/docs"

docs.SwaggerInfo.Host     = os.Getenv("API_HOST")
docs.SwaggerInfo.BasePath = "/api/v1"
```

See the full CLI notes in [references/swag-cli.md](./references/swag-cli.md).

## General API Info

Put top-level annotations in `main.go` or the file passed via `-g`:

```go
// @title           My API
// @version         1.0
// @description     Short description of the API.
// @host            localhost:8080
// @BasePath        /api/v1
// @schemes         http https

// @contact.name    API Support
// @contact.email   support@example.com
// @license.name    Apache 2.0

// @securityDefinitions.apikey Bearer
// @in header
// @name Authorization
// @description Type "Bearer" followed by a space and the JWT token.
```

## Operation Annotations

Annotate each handler function. A standard doc comment such as `// ShowAccount godoc` should precede the `@` annotations so `swag fmt` can format them consistently.

```go
// ShowAccount godoc
// @Summary      Get account by ID
// @Description  Returns account details for the given ID.
// @Tags         accounts
// @Accept       json
// @Produce      json
// @Param        id      path   int     true   "Account ID"
// @Param        filter  query  string  false  "Optional search filter"
// @Success      200  {object}  model.Account
// @Success      204  "No content"
// @Failure      400  {object}  api.ErrorResponse
// @Failure      404  {object}  api.ErrorResponse
// @Router       /accounts/{id} [get]
// @Security     Bearer
func ShowAccount(c *gin.Context) {}
```

`@Param` format:

```text
@Param <name> <in> <type> <required> "<description>" [attributes]
```

Common locations:

| `<in>` | Usage |
| --- | --- |
| `path` | URL path segment |
| `query` | URL query string |
| `body` | Request body — use a struct type |
| `header` | HTTP header |
| `formData` | Multipart/form field |

Optional attributes include `default(v)`, `minimum(n)`, `maximum(n)`, `minLength(n)`, `maxLength(n)`, `Enums(a,b,c)`, `example(v)`, and `collectionFormat(multi)`.

## Security Definitions

Define security schemes once at the API level and apply them per endpoint with `@Security`:

```go
// @securityDefinitions.apikey Bearer
// @in header
// @name Authorization

// @securityDefinitions.apikey ApiKeyAuth
// @in header
// @name X-API-Key

// @securityDefinitions.basic BasicAuth

// @securityDefinitions.oauth2.authorizationCode OAuth2
// @authorizationUrl https://example.com/oauth/authorize
// @tokenUrl https://example.com/oauth/token
// @scope.read Read access
// @scope.write Write access
```

Endpoint usage:

```go
// @Security Bearer
// @Security OAuth2[read, write]
// @Security BasicAuth && ApiKeyAuth
```

## Struct Tags

Use struct tags to enrich generated schemas without changing core Go types:

```go
type CreateUserRequest struct {
    Name   string `json:"name" example:"Jane Doe" minLength:"2" maxLength:"100"`
    Role   string `json:"role" enums:"admin,user,guest" example:"user"`
    Age    int    `json:"age" minimum:"18" maximum:"120"`
    Avatar []byte `json:"avatar" swaggertype:"string" format:"base64"`
    Secret string `json:"-" swaggerignore:"true"`
}
```

## Common Mistakes

| Mistake | Why it breaks | Fix |
| --- | --- | --- |
| Missing `_ "yourmodule/docs"` import | Schema is not registered | Add the import where the server is wired |
| Stale generated `docs/` output | Docs drift from implementation | Re-run `swag init` after annotation changes |
| `@Param body` with a primitive type | `swag` cannot derive a full schema | Use a named struct for body payloads |
| Missing `@Security` on protected routes | Consumers do not see auth requirements | Add `@Security` to each authenticated endpoint |
| General API annotations in the wrong file | Spec is missing title/host/base path | Move them to the file passed to `swag init -g` |
| Using generic maps where a schema is expected | Generated schema is weak or ambiguous | Prefer named structs where possible |

## Production Notes

- Treat generated docs as part of the API contract
- Gate or disable Swagger UI in production when appropriate
- Keep examples and response models synchronized with real handlers
- Prefer explicit documented error responses over undocumented fallback behavior

## Cross-References

- Use `golang-security` when the Swagger endpoint itself needs production hardening, auth gating, or environment-based exposure rules
- Use `api-governance` when the task is about broader API lifecycle policy, standards, or review gates
- Use `go-builder` when the work also involves broader Go service setup or architecture decisions
- Use `openapi-specification` when the generated or maintained OpenAPI document must be reviewed against OAS 3.2+ syntax, JSON Schema alignment, references, examples, or validation/linting expectations

## Verification Checklist

- [ ] The skill name matches the directory: `golang-openapi`
- [ ] The description starts with `Use when ...`
- [ ] The skill refers only to local skills or plain external tools/docs
- [ ] The setup examples, annotation examples, and UI wiring remain internally consistent
- [ ] The guidance treats generated OpenAPI as a maintained contract, not a one-time artifact
