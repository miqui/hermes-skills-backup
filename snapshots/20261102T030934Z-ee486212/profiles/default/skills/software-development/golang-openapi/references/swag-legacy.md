# swag Legacy Reference (annotations, security, struct tags)

> **Legacy.** swag v1 (v1.16.x) emits **Swagger 2.0**. swag v2 (v2.0.0-rc6, release candidate) has opt-in **OpenAPI 3.1** output. **Neither emits 3.2.** Never relabel the `swagger`/`openapi` field to `3.2.0`. For the 3.2 workflow see [../SKILL.md](../SKILL.md); for document rules see `openapi-specification`. CLI/generics/config: [swag-cli.md](./swag-cli.md).

## Setup

```bash
swag init                        # docs/ with docs.go, swagger.json, swagger.yaml
swag init -g cmd/api/main.go     # general info not in main.go
swag fmt                         # format annotation comments
```

```go
import _ "yourmodule/docs"     // blank: registers spec
import docs "yourmodule/docs"  // named: override SwaggerInfo at runtime
```

## General API Info

Top-level annotations go in `main.go` or the file passed via `-g`:

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

`@host`, `@BasePath`, `@schemes` are Swagger 2.0 concepts (become `servers` in OAS 3.x).

## Operation Annotations

A doc comment such as `// ShowAccount godoc` should precede the `@` annotations so `swag fmt` formats them.

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

`@Param <name> <in> <type> <required> "<description>" [attributes]`

| `<in>` | Usage |
| --- | --- |
| `path` | URL path segment |
| `query` | URL query string |
| `body` | Request body; use a struct type |
| `header` | HTTP header |
| `formData` | Multipart/form field |

Attributes: `default(v)`, `minimum(n)`, `maximum(n)`, `minLength(n)`, `maxLength(n)`, `Enums(a,b,c)`, `example(v)`, `collectionFormat(multi)`.

## Security Definitions

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

Per endpoint:

```go
// @Security Bearer
// @Security OAuth2[read, write]
// @Security BasicAuth && ApiKeyAuth
```

3.2-only security features (e.g. OAuth2 device flow) cannot be expressed through swag.

## Struct Tags

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
| Missing `_ "yourmodule/docs"` import | Spec not registered | Import where the server is wired |
| Stale generated `docs/` | Docs drift | Re-run `swag init` after annotation changes |
| `@Param body` with a primitive | No full schema | Use a named struct |
| Missing `@Security` on protected routes | Auth not documented | Add per endpoint |
| General info in the wrong file | Missing title/host/base path | Use the `-g` file |
| Generic maps where a schema is expected | Weak schema | Prefer named structs |
