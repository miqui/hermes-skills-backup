---
name: go-builder
description: Use when building or modifying Go services, Lambda handlers, or CLIs with opinionated guidance on framework choice, project layout, dependency management, Docker, testing, and delivery readiness.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [go, golang, chi, lambda, cli, docker, slog, modules]
    related_skills: [api-governance, local-git-workflow, golang-coding-style, golang-lint, golang-testing, golang-security, golang-concurrency, golang-troubleshooting]
---

# Go Builder

## Overview

Use this skill when building or modifying Go HTTP services, AWS Lambda functions, or CLI tooling and you want strong defaults for framework selection, package layout, dependency hygiene, Docker packaging, testing, and pre-delivery verification.

This skill is intentionally portable. It covers Go implementation guidance, not machine-specific GitHub workflow policy. If the active environment defines a mandatory local wrapper for repository creation, pushes, or pull requests, load and follow `local-git-workflow` in addition to this skill.

## When to Use

- Building a new Go HTTP service, Lambda function, or CLI from scratch
- Standardizing an existing Go project around clearer package layout and dependency hygiene
- Choosing between `net/http`, `chi`, Echo, Gin, Fiber, or Encore.go for a new service
- Adding Docker packaging, `.dockerignore`, or runtime-hardening patterns to a Go project
- Tightening code review expectations, logging, configuration loading, and validation practices
- Preparing a Go project for reliable local verification and delivery

Do not use this skill for:
- Non-Go projects
- Pure planning work where no implementation guidance is needed
- Deep debugging sessions where `golang-troubleshooting` should lead the workflow
- Tasks that are primarily API governance or contract design rather than Go implementation details
- Machine-specific GitHub workflow rules; use `local-git-workflow` for those

## HTTP Framework Selection

Before choosing a framework, apply these criteria:

**net/http (stdlib)**
Best for simple services or when minimising dependencies is a hard requirement. No external deps, stable API. Since Go 1.22 `http.ServeMux` supports method and path-wildcard patterns (`GET /users/{id}`, `r.PathValue("id")`), so a router dependency is often unnecessary. Validation, binding, and middleware chaining remain manual. Production defaults, `slog`, graceful shutdown, and a Dockerfile: see [references/http-service.md](./references/http-service.md).

**chi (github.com/go-chi/chi/v5)** — default choice when stdlib `ServeMux` is not enough (middleware groups, sub-routers)
Best for enhanced routing while staying close to the standard library. Full net/http compatibility means any stdlib middleware works out of the box. Composable, minimal, idiomatic. Does not include validation or body binding — pair with go-playground/validator and encoding/json. Choose when net/http middleware compatibility matters and you prefer minimal, composable tools over a full framework.

**Echo (github.com/labstack/echo/v4)**
Best for REST APIs with clean design and good documentation. Uses standard context.Context, error-returning handlers are idiomatic, excellent OpenAPI integration. Smaller community than Gin. Choose when you want OpenAPI generation baked in or prefer error-return handlers.

**Gin (github.com/gin-gonic/gin)**
Best for general-purpose API development on a single service where community resources matter. Large ecosystem, built-in validation, and extensive examples. Uses a custom context type (not standard `context.Context`); middleware quality varies; framework lock-in makes migration harder. Choose when community support and built-in binding are worth the tradeoffs.

**Fiber (github.com/gofiber/fiber; check the current major version)**
Best for teams migrating from Node.js/Express or for high-throughput applications where microseconds matter. Built on fasthttp — exceptional performance, zero-alloc hot paths. Breaks net/http middleware compatibility; non-idiomatic to experienced Go developers. Choose only when maximum raw performance justifies the fasthttp tradeoffs, or when onboarding a JavaScript team.

**Encore.go**
Best for distributed systems, microservices, and event-driven architectures needing automatic infrastructure provisioning. Type-safe service communication, auto-discovered services, built-in Pub/Sub/cron/DB primitives, distributed tracing, auto-generated API docs. Uses comment annotations as a unique pattern; works best when fully embracing its conventions. Choose for multi-service systems where infrastructure automation is a priority.

## Stack

- Latest stable Go (support the current and previous minor release at minimum; keep the `go` line in `go.mod` at the oldest version you test) with explicit types on exported symbols; `any` only when type inference is genuinely required
- `chi` for HTTP routing by default when stdlib `ServeMux` is not enough
- AWS Lambda with `aws-lambda-go`; prefer `provided.al2023` over deprecated runtimes
- `aws-sdk-go-v2` with explicit error handling and `context.Context` on AWS calls
- `go-playground/validator/v10` for request validation when schema-style validation is needed
- `cobra` plus `lipgloss` for CLI tools; add config libraries only when configuration files are actually needed
- `log/slog` for logging
- Configuration via environment or explicit config loading, never hardcoded values
- Go modules as the source of truth (`go.mod` + `go.sum`)
- `go run` for one-off tools; prefer tool directives in modern Go over legacy `tools.go` patterns

## Dependency Management

Always use `go mod`. Never vendor unless the deployment target requires it.

```bash
go mod init github.com/user/project
go get github.com/go-chi/chi/v5
go get -tool github.com/golangci/golangci-lint/v2/cmd/golangci-lint
go mod tidy
go run ./cmd/server
go tool golangci-lint run
go test ./...
```

`go.mod` is the single source of truth. Tool dependencies belong in `go.mod` via `go get -tool` in modern Go; avoid maintaining legacy `tools.go` blank-import files unless the repository already depends on that pattern. golangci-lint's own docs recommend binary installation over `go get -tool`/`go install` (not guaranteed to work; see `golang-lint`).

## Project Structure

New projects should be created in the user's standard development workspace for the active environment.

Standard layout for an HTTP service:

```text
project/
  cmd/
    server/
      main.go
  internal/
    handlers/
    middleware/
    models/
    services/
    config/
    logging/
  tests/
  Dockerfile
  go.mod
  go.sum
  .env.example
```

Standard layout for Lambda:

```text
project/
  cmd/
    function/
      main.go
  internal/
    handler/
    service/
    config/
  events/
  go.mod
  go.sum
  template.yaml
```

Standard layout for CLI:

```text
project/
  cmd/
    root.go
    serve.go
    version.go
  internal/
    config/
    output/
  main.go
  go.mod
  go.sum
```

## Code Style

- Follow Effective Go, Google Go Style, and `go.dev/wiki/CodeReviewComments`
- `gofmt` / `goimports` is non-negotiable
- Lint with `golangci-lint` v2; use the `golang-lint` skill and its bundled `.golangci.yml` as the baseline rather than hand-picking linters
- `MixedCaps` for exported identifiers, `mixedCaps` for unexported names
- File names in `lower_snake_case.go`
- One package = one responsibility; use `internal/` for non-exported packages
- Accept interfaces where needed, return concrete types by default
- `context.Context` is the first parameter when needed
- Wrap errors with `%w`; inspect with `errors.Is` / `errors.As`
- Avoid naked returns except in very short functions
- When asked to generate code, return complete files or clearly scoped edits

## Code Review Guidelines

Apply these consistently when writing or reviewing Go code:

**Formatting**
- run `gofmt` / `goimports`
- keep imports grouped cleanly

**Comments**
- exported names need doc comments that start with the symbol name and end with a period
- package comments belong next to the `package` clause

**Naming**
- preserve initialism casing such as `URL`, `HTTP`, `ID`
- package names stay short, lowercase, and specific
- receiver names stay short and consistent

**Errors**
- never discard errors with `_`
- error strings stay lowercase with no trailing punctuation
- prefer returned errors over panics for normal control flow

**Error flow**
- handle errors early
- minimize indentation on the happy path

**Context**
- pass `context.Context` explicitly
- do not store it in structs

**Interfaces**
- define interfaces in consuming packages
- return concrete implementations

**Receivers**
- use pointer receivers for mutation, large structs, or sync fields
- do not mix pointer and value receivers on the same type

**Slices**
- use nil slices internally (`var s []T`; `len`, `append`, and `range` work on nil); return a non-nil empty slice (`[]T{}`) at JSON/API boundaries, since nil marshals to `null`

**Concurrency**
- prefer synchronous functions by default
- make goroutine lifetime obvious when concurrency is needed

**Crypto**
- use `crypto/rand` for security-sensitive randomness

**Tests**
- failures should show inputs, got, and want
- use table-driven tests for repetitive case matrices

## Delivery and Git Workflow

This skill covers code readiness, not local GitHub policy.

Before delivery:

1. confirm the project builds
2. confirm relevant tests pass
3. confirm formatting and linting expectations are met
4. confirm docs and env examples match the implementation
5. if the active environment mandates a local Git or GitHub wrapper workflow, load and follow `local-git-workflow`

## Related Skills

- Use `api-governance` when the task depends on API contract design or lifecycle decisions
- Use `golang-troubleshooting` when builds fail, tests break, or runtime behavior is unclear
- Use `golang-coding-style`, `golang-lint`, `golang-testing`, `golang-security`, and `golang-concurrency` for their respective concerns
- Use `local-git-workflow` when repository creation, pushes, or pull requests must follow this machine's required wrapper script

## Common Pitfalls

1. Choosing a framework before clarifying constraints.
   Start by checking whether the project needs stdlib compatibility, built-in binding, maximum throughput, or multi-service infrastructure automation. Default to `chi` unless there is a concrete reason not to.

2. Mixing Go architecture guidance with machine-specific Git policy.
   Keep `go-builder` focused on Go implementation choices; load `local-git-workflow` when write-side GitHub workflow rules matter.

3. Treating `go.mod` as secondary.
   `go.mod` and `go.sum` are the source of truth. Run `go mod tidy`, commit both files, and avoid stale dependency patterns.

4. Shipping code without verification.
   Before declaring work complete, verify formatting, build, vet, tests, and any Docker artifacts you introduced.

5. Using examples as rigid templates.
   The HTTP, Lambda, CLI, config, and logging sections are strong defaults, not mandatory boilerplate. Adapt paths and entrypoints to the actual repo.

6. Overlooking exported-name and error-string conventions.
   Go style problems often come from naming, comments, and lowercase error strings rather than compilation failures.

## Usage Checks

- [ ] Framework choice is justified by a stated constraint (stdlib compatibility, binding, throughput, multi-service)
- [ ] `go build ./...`, `go vet ./...`, and `go test ./...` pass; `go mod tidy` leaves no diff
- [ ] `gofmt`/`goimports` and `golangci-lint run` are clean on touched files
- [ ] HTTP servers set `ReadHeaderTimeout` and shut down gracefully
- [ ] Dockerfile and `.dockerignore` exist and the image builds when container packaging is in scope
- [ ] README and `.env.example` match the actual commands, env vars, and layout
- [ ] Output is complete files or clearly scoped edits, not pseudo-code
