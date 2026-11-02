---
name: grpc-api
description: Use when designing, building, reviewing, or troubleshooting protobuf + gRPC APIs, including .proto contract design, schema style, service/RPC modeling, code generation, compatibility, streaming, errors, validation, gateways, observability, and runtime implementation handoff.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [grpc, protobuf, proto3, proto-editions, buf, codegen, streaming, grpc-gateway, connectrpc, api-design]
    related_skills: [api-governance, openapi-api-designer, graphql-api, event-driven-api-design, go-builder, python-dev, spring-boot-engineer, golang-testing, java-coding-standards, code-performance-engineering, application-authorization]
---

# Protobuf + gRPC API Design

## Overview

Use this skill when the API contract is primarily a protobuf schema exposed through gRPC or a closely related protocol such as Connect, gRPC-Web, grpc-gateway, or Envoy transcoding. Treat `.proto` files as durable API contracts, not implementation artifacts: package names, field numbers, enum defaults, request/response messages, status codes, metadata, deadlines, and streaming semantics all shape client behavior.

This skill is contract-first and language-agnostic at the schema layer. Pair it with runtime-specific skills for implementation:
- `go-builder` and `golang-testing` for Go services, clients, and integration tests
- `python-dev` for Python services, generated-code packaging, and tooling
- `spring-boot-engineer` plus `java-coding-standards` for Java/Spring or JVM-based gRPC services
- `api-governance` when lifecycle, publication, ownership, compatibility policy, or developer portal concerns matter
- `code-performance-engineering` when latency, fan-out, streaming, load balancing, payload size, deadlines, or tail behavior are central

For house-style guidance distilled from Uber's prototool style guide, see `references/protobuf-style-guide.md`. Use it as a style influence, not as an unmodified mandate; adapt it to the repository's existing conventions and Buf lint profile.

## When to Use

Use this skill when the task involves:

- Designing or reviewing protobuf files, packages, messages, enums, services, or RPCs
- Creating a new gRPC API or refactoring an existing one
- Choosing between unary, server-streaming, client-streaming, and bidirectional streaming RPCs
- Defining request/response message conventions, pagination, batch operations, or long-running operations
- Introducing Buf, `protoc`, code generation, linting, or breaking-change checks
- Modeling canonical gRPC status codes, rich errors, validation failures, auth failures, and quota failures
- Designing metadata, auth, deadlines, cancellation, retries, idempotency, interceptors, or observability
- Supporting browser or HTTP/JSON consumers through Connect, grpc-gateway, gRPC-Web, or transcoding
- Debugging schema compatibility, generated-code imports, gateway mismatches, status-code behavior, or streaming semantics

Do not use this skill as the only guide for:

- Pure REST/OpenAPI work with no protobuf/gRPC contract; use `openapi-api-designer` or `openapi-specification`
- Pure GraphQL work; use `graphql-api`
- Event/message/stream contracts where AsyncAPI, CloudEvents, Kafka, queues, or webhooks are primary; use `event-driven-api-design`
- Generic backend work where gRPC is incidental and no contract choices are being made

## Core Principles

1. **Contract first, generated code second.** Design the `.proto` API for consumers and compatibility before optimizing server implementation convenience.
2. **Compatibility is stricter than normal refactoring.** Field numbers, field names for JSON mappings, enum defaults, package names, RPC signatures, and streaming choices are API surface.
3. **Prefer explicit semantics over clever schemas.** Document optionality, defaults, units, ID formats, validation, idempotency, and side effects.
4. **Unary is the default.** Use streaming only when its lifecycle, backpressure, retry, load-balancing, and operational implications are justified.
5. **Deadlines, cancellation, retries, and auth are API behavior.** They belong in design and tests, not as late middleware decoration.
6. **Make generation reproducible.** Use Buf or a documented repo-standard `protoc` flow so generated code does not drift.
7. **Expose HTTP/JSON deliberately.** Gateway paths rarely preserve native gRPC semantics perfectly; document differences.

## Design Workflow

### 1. Frame the API product

Before writing `.proto` files, clarify:

- Business capability and owning domain
- Known consumers: internal services, mobile apps, browser apps, partner clients, batch jobs, AI/tool clients
- Stability level: experimental, beta, internal stable, public stable
- Expected interaction style: request/response, list/search, batch, long-running, progressive response, upload, duplex session
- Latency, throughput, message size, retention, and retry expectations
- Whether non-gRPC access is required through HTTP/JSON, gRPC-Web, or Connect

If ownership, consumers, or stability are unclear for a non-trivial API, pause and pair with `api-governance` before locking package names and versioning.

### 2. Choose package and version layout

Use domain-oriented, versioned packages for published or stable contracts:

```proto
syntax = "proto3";

package acme.payments.v1;

option go_package = "github.com/acme/payments/gen/go/acme/payments/v1;paymentsv1";
option java_multiple_files = true;
option java_package = "com.acme.payments.v1";
option java_outer_classname = "PaymentsProto";
```

Guidelines:

- Prefer short lowercase package sub-names using letters and digits; avoid underscores in package segments.
- Include a version suffix such as `v1` for any contract expected to outlive one implementation.
- Keep directory paths aligned with package names: `proto/acme/payments/v1/payment_service.proto`.
- Use domain names, not team names or storage technologies.
- Avoid package segments that collide with language keywords or runtime packages. In Python, never use a top-level package root such as `grpc.*`; it collides with `grpcio`.
- For greenfield work, use `proto3` unless the repository has intentionally standardized on protobuf Editions.

### 3. Organize files predictably

A strong default layout:

```text
project/
  proto/
    acme/payments/v1/
      payment.proto
      payment_service.proto
  gen/
    go/
    python/
    java/
  src/ or internal/
  buf.yaml
  buf.gen.yaml
  README.md
```

File guidance:

- Use `lower_snake_case.proto` file names.
- Keep source `.proto` files separate from generated code.
- Keep each stable package internally consistent; do not mix multiple packages in one directory.
- Put service definitions and their RPC-specific request/response messages close together.
- Put shared domain messages and enums in supporting files.
- Alphabetize imports and keep import roots consistent from the repo's proto root.

### 4. Model RPCs intentionally

Choose the simplest RPC shape that matches the interaction:

| RPC shape | Use when | Avoid when |
| --- | --- | --- |
| Unary | Standard bounded request/response, create/read/update/delete, validation, commands | You truly need progressive results or upload/download streams |
| Server-streaming | One request produces many results over time, progress updates, watch-like reads | Pagination or polling would be simpler and good enough |
| Client-streaming | Client uploads a sequence and receives one final result | A bounded repeated field or chunked unary protocol would be simpler |
| Bidirectional streaming | Both sides need independent asynchronous message flow | You are future-proofing or building a workflow that is actually request/reply |

RPC conventions:

- Name RPCs in `PascalCase`, usually verb+noun: `GetPayment`, `ListPayments`, `CreatePayment`.
- Prefer unique request and response messages per RPC: `GetPaymentRequest`, `GetPaymentResponse`.
- Do not reuse request/response messages across unrelated RPCs just to reduce duplication; it couples their evolution.
- Document side effects, preconditions, idempotency, and retry expectations on mutating RPCs.
- For long-running work, model operation state, polling, cancellation, or progress updates explicitly rather than hiding async work behind a misleading unary response.

Example:

```proto
// PaymentService manages payment authorization and settlement workflows.
service PaymentService {
  // Gets a payment by its stable payment ID.
  rpc GetPayment(GetPaymentRequest) returns (GetPaymentResponse);

  // Creates a payment authorization request.
  rpc CreatePayment(CreatePaymentRequest) returns (CreatePaymentResponse);
}

message GetPaymentRequest {
  string payment_id = 1;
}

message GetPaymentResponse {
  Payment payment = 1;
}
```

## Protobuf Schema Design Rules

### Messages and fields

- Use `PascalCase` for message names and `lower_snake_case` for field names.
- Model semantic domain concepts, not common field bags or ORM/table structures.
- Avoid single-field wrapper messages unless the message has real protocol/domain meaning.
- Document units, formats, optionality, validation rules, and default behavior for non-obvious fields.
- Prefer domain IDs such as `payment_id`, `customer_id`, and `account_id`; document if they are UUIDs, ULIDs, opaque strings, or external IDs.
- Prefer `int64 amount_minor` plus `currency_code` or a dedicated money type over floating-point currency.
- Name `google.protobuf.Timestamp` fields as `*_time` or a similarly clear time concept.
- Name `google.protobuf.Duration` fields as `*_duration` or a similarly clear duration concept.
- Avoid `json_name`; protobuf JSON mapping should remain predictable.

### Presence and optionality

Proto scalar defaults can hide whether a caller intentionally set a value. When presence matters:

- Use `optional` scalar fields deliberately in proto3/editions-compatible repos.
- Use wrapper types only when the repository standard or target language requires them.
- Use `FieldMask` for partial updates instead of treating default scalar values as "not provided".
- Document whether empty strings, zero values, and absent fields are accepted, rejected, or defaulted.

### Enums

- Use `PascalCase` enum names and `UPPER_SNAKE_CASE` enum values.
- Prefix enum values with the enum name to avoid cross-language scoping collisions.
- Do not use `allow_alias` unless the repository already has a strong reason.
- Include a zero value that means unspecified/invalid, such as `PAYMENT_STATUS_UNSPECIFIED = 0`.
- Treat new enum values as compatibility-sensitive: older clients may receive unknown values.
- Add explicit semantic values only when they are real domain states.

```proto
enum PaymentStatus {
  PAYMENT_STATUS_UNSPECIFIED = 0;
  PAYMENT_STATUS_PENDING = 1;
  PAYMENT_STATUS_AUTHORIZED = 2;
  PAYMENT_STATUS_SETTLED = 3;
  PAYMENT_STATUS_FAILED = 4;
}
```

### oneof, map, repeated, and Any

- Use `oneof` only for true mutual exclusivity in the domain.
- Do not move existing fields into or out of a `oneof` in a stable package; that is a breaking change for many clients.
- Use `map` only when arbitrary key lookup is the model; prefer `repeated` messages when ordering, validation, evolution, or per-entry metadata matters.
- Bound and document `repeated` fields; unbounded lists become performance and memory risks.
- Avoid `google.protobuf.Any` in public contracts unless you have a type registry, validation policy, and versioning story.

### Well-known types

Use well-known types for their intended semantics:

- `google.protobuf.Timestamp` for instants in time
- `google.protobuf.Duration` for elapsed time or timeouts
- `google.protobuf.FieldMask` for partial update paths
- `google.protobuf.Empty` only when the absence of request/response fields is intentional and future evolution is unlikely
- `google.protobuf.Struct`/`Value` only for genuinely schemaless data, not to avoid schema design

## Schema Evolution and Compatibility

For stable packages, prefer additive evolution:

- Add new fields with new field numbers.
- Never reuse field numbers.
- Never change the meaning, type, label, or JSON-visible name of an existing field casually.
- Avoid renaming packages, messages, fields, enum values, services, or RPCs in stable contracts.
- Deprecate before removal, and keep generated-code compatibility in mind.
- Reserve removed field numbers and names when actual removal is necessary, especially if protobuf JSON is or may become part of the API.
- Run breaking-change checks against the published baseline before merging.

Breaking changes include:

- Deleting or renaming a package, message, enum, field, service, or RPC
- Reusing or changing a field number
- Changing a field type, cardinality/label, or oneof membership
- Changing an RPC request type, response type, or streaming mode
- Changing enum value numbers or meanings
- Changing gateway-visible paths, JSON names, error semantics, or required metadata in ways clients depend on

For incompatible redesigns, create a new versioned package such as `acme.payments.v2` and plan migration instead of mutating `v1` in place.

## Style Guide Defaults

When a repository does not already have a protobuf style guide, use these defaults and document that you are doing so:

- Two-space indentation.
- `proto3` for new definitions unless protobuf Editions is a known repo standard.
- `lower_snake_case.proto` files.
- Package paths mirror package names.
- Package names are short, lowercase, domain-oriented, and versioned.
- File order: license/header if needed, `syntax`, `package`, file options, imports, definitions.
- Options and imports are alphabetized where practical.
- Messages/services/RPCs use `PascalCase`; fields and oneofs use `lower_snake_case`; enum values use prefixed `UPPER_SNAKE_CASE`.
- Services and RPCs have comments that explain purpose, side effects, and constraints.
- Prefer top-level reusable messages/enums over nested types unless the nested type is truly private to one message forever.
- Prefer unique request/response messages per RPC.
- Prefer unary RPCs unless streaming is clearly justified.

See `references/protobuf-style-guide.md` for more detailed style guidance and caveats from the Uber/prototool reference.

## Tooling and Code Generation

### Prefer Buf for new work

Use Buf when starting fresh or when the repo is already close to contract-first protobuf workflows:

```yaml
# buf.yaml
version: v2
modules:
  - path: proto
lint:
  use:
    - STANDARD
breaking:
  use:
    - FILE
```

```yaml
# buf.gen.yaml
version: v2
plugins:
  - remote: buf.build/protocolbuffers/go
    out: gen/go
  - remote: buf.build/grpc/go
    out: gen/go
```

Buf benefits:

- Reproducible generation across machines and CI
- Linting and formatting conventions
- Breaking-change checks
- Cleaner multi-language generation than ad hoc `protoc` scripts
- Good monorepo and module ergonomics

### When raw protoc is acceptable

Use direct `protoc` when:

- The repository already has a mature checked-in `protoc` workflow
- The target ecosystem requires a plugin flow not yet covered by Buf
- The task is small and introducing Buf would be unrelated churn

Even then, keep generation reproducible with scripts, Make targets, or CI commands. Do not leave codegen as a hand-run shell incantation.

### Generated-code policy

Clarify whether generated code is committed. Both policies can work:

- Commit generated code when downstream consumers need source-only installs, generated clients are published from this repo, or CI/package systems expect generated files.
- Do not commit generated code when every build reliably generates it and packages are published as artifacts.

Whichever policy the repo uses, verify generated-code drift in CI.

## Errors and Validation

### Canonical status codes

Map domain failures to canonical gRPC statuses intentionally:

- `INVALID_ARGUMENT` for request validation failures independent of current state
- `NOT_FOUND` for missing resources
- `ALREADY_EXISTS` for uniqueness conflicts
- `FAILED_PRECONDITION` for state-dependent business constraints
- `PERMISSION_DENIED` for authorization failures
- `UNAUTHENTICATED` for missing or invalid credentials
- `RESOURCE_EXHAUSTED` for quotas, rate limits, or capacity limits
- `UNAVAILABLE` for transient backend or dependency unavailability
- `DEADLINE_EXCEEDED` when the operation times out
- `CANCELLED` when the caller cancels the operation
- `UNIMPLEMENTED` for unsupported RPCs/features
- `INTERNAL` only for unexpected server faults

Do not collapse every server-side problem into `INTERNAL`.

### Rich errors

Use `google.rpc.Status` and rich error details when clients need structured remediation:

- field violations for validation errors
- retry info for retryable failures
- quota failure details for quota/rate-limit problems
- resource info for missing or conflicting resources
- localized/user-facing messages only when the platform intentionally supports them

Keep sensitive implementation details out of error messages. Log diagnostics server-side with correlation IDs.

### Validation

- Validate at the service boundary before domain side effects.
- Prefer a standard validation approach such as `protovalidate` when it fits the repo.
- Keep validation changes compatibility-aware; tightening validation can break existing clients.
- Test both schema-level validation and domain/business preconditions.

## Metadata, Auth, and Security

Use metadata for request context, not domain data:

- auth credentials or bearer tokens
- request/correlation IDs
- trace context
- tenant or organization context when policy allows it
- idempotency keys when the API standard places them in metadata

Security guidance:

- Centralize authn/authz in interceptors or middleware where possible.
- Keep object-level authorization in domain/service policy layers so alternate RPC paths cannot bypass it.
- Use mTLS or service identity for service-to-service calls when the platform supports it.
- Document required metadata keys and formats.
- Do not log sensitive metadata or payload fields by default.
- Treat generated clients as public API consumers if they leave the service boundary.

> **Authorization model scope:** This skill owns interceptor wiring for authn/authz, domain-object check placement, and mapping authorization outcomes to canonical gRPC status codes (`PERMISSION_DENIED`, `UNAUTHENTICATED`). For the underlying authorization model — RBAC/ABAC/ReBAC design, role and permission administration lifecycle, and policy enforcement point architecture — load `application-authorization`.

## Deadlines, Cancellation, Retries, and Idempotency

- Clients should set explicit deadlines for every call.
- Servers should observe cancellation promptly and stop expensive downstream work.
- Do not hide indefinite waits behind unary RPCs.
- Retry only idempotent operations or failures explicitly documented as retry-safe.
- Use idempotency keys for creates or commands that clients/gateways may retry.
- Document whether retry policy lives in clients, service config, proxies, or load balancers.
- Avoid retry storms by respecting deadlines, backoff, jitter, and server overload signals.

## Streaming API Design

Before choosing streaming, answer:

- Who controls pacing and flow control?
- What ends the stream successfully?
- Can messages be duplicated, skipped, or delivered out of order?
- How does the client resume after disconnect?
- What are heartbeat/progress semantics?
- How are partial failures represented?
- How do load balancers, proxies, and deployments handle long-lived streams?
- What metrics prove streams are healthy?

Prefer:

- Server-streaming for progressive result delivery, watch APIs, or progress updates when pagination/polling is insufficient
- Client-streaming for large uploads or ingest when repeated unary chunks are not enough
- Bidirectional streaming only for true duplex protocols

Common streaming pitfalls:

- Premature bidi streaming
- No termination contract
- Ignoring backpressure and cancellation
- Long-lived streams that break deploys or load balancing
- Oversized messages instead of chunking
- No resume token or replay story

## HTTP/JSON, Browser, and Gateway Concerns

Use an adapter only when there is a real consumer need:

- **grpc-gateway**: useful in Go-centric stacks that want REST-like HTTP/JSON from protobuf annotations
- **Envoy transcoding**: useful when HTTP/JSON mapping belongs in infrastructure
- **Connect/ConnectRPC**: useful for one contract across gRPC-like, JSON-friendly, and browser-accessible clients
- **gRPC-Web**: useful when browser clients need gRPC-style calls through a compatible proxy/server

Gateway review questions:

- Are HTTP paths and methods consumer-friendly, or just RPC names over HTTP?
- Are errors mapped predictably between gRPC status and HTTP status/body?
- Are streaming RPCs supported, downgraded, or unavailable?
- Are metadata/auth semantics preserved?
- Are protobuf JSON mapping defaults acceptable for clients?
- Are field names, enum values, timestamps, and 64-bit integers safe for JSON consumers?

Do not assume HTTP/JSON parity is free. Document the supported surface and differences.

## Observability and Operations

Production gRPC services should usually include:

- Health checking
- Server reflection where safe and useful for internal tooling
- Structured logs with method name, status code, peer, latency, and request/correlation ID
- Metrics by service, method, status, latency bucket, message size, and stream duration
- Distributed tracing with trace context propagation
- Deadline exceeded, cancellation, retry, and overload visibility
- Alerting for high error rates, latency, saturation, stream failures, and dependency failures

Avoid logging full request/response payloads unless explicitly scrubbed and approved.

## Testing Strategy

### Contract/tooling tests

- `buf lint` or repo-standard proto lint
- `buf breaking` or repo-standard compatibility checks against the published baseline
- `buf generate` or repo-standard generation in CI
- Generated-code drift checks when generated files are committed
- Example/message validation where supported

### Service tests

- Handler tests with real generated clients where feasible
- Validation and canonical status-code mapping
- Auth/metadata behavior through interceptors
- Unauthorized access: missing credentials (`UNAUTHENTICATED`) and insufficient permissions (`PERMISSION_DENIED`)
- Cross-tenant and object-level access: verify one tenant/principal cannot read or mutate another's resources
- Role/permission change propagation: confirm that downgraded or revoked roles take effect without requiring a service restart
- Deadlines and cancellation
- Idempotency behavior for retryable mutations
- Gateway behavior if HTTP/JSON exposure exists

### Streaming tests

- Happy path stream completion
- Client cancellation
- Server error mid-stream
- Slow consumer/backpressure behavior
- Resume/retry behavior where promised
- Resource cleanup after disconnect

## Language-Specific Pairing Guidance

### Go

Load `go-builder`, `golang-testing`, and optionally `golang-concurrency`, `golang-security`, or `golang-lint`.

Common tools:

- `google.golang.org/grpc`
- `connectrpc/connect-go`
- `grpc-gateway`
- Buf remote plugins for Go protobuf and gRPC generation

### Python

Load `python-dev`, and optionally `python-observability`.

Common tools:

- `grpcio`
- `grpcio-tools` or Buf-managed generation
- `betterproto` only when the repo has standardized on it or there is a clear DX reason

Python pitfalls:

- Do not use a proto package rooted at `grpc.*`; it collides with the `grpcio` runtime package.
- With a `src/` layout and `uv`, include a `[build-system]` table so the project installs in editable mode and generated modules are importable. See `references/python-buf-minimal-starter.md`.

### Java / JVM

Load `spring-boot-engineer` and `java-coding-standards`.

Common tools:

- `grpc-java`
- Gradle or Maven protobuf plugins
- Spring integration only when it fits the stack; do not force Spring abstractions onto simple gRPC services

### TypeScript / Browser

Consider ConnectRPC or gRPC-Web when browser access matters. Review JSON mapping, streaming support, auth propagation, and generated-client ergonomics before choosing native gRPC assumptions.

## Suggested Delivery Workflow

1. Clarify consumers, ownership, stability, and exposure model.
2. Choose package/version/directory layout.
3. Draft `.proto` files with service/RPC/message/enum style rules.
4. Add or update Buf/protoc generation config.
5. Generate code and wire runtime-specific service stubs.
6. Add validation, status-code mapping, auth/interceptors, deadlines, and observability.
7. Add contract, unit, integration, and streaming tests as applicable.
8. Run lint, breaking-change checks, generation, and runtime smoke tests before delivery.

## Common Pitfalls

1. **Treating `.proto` changes like ordinary refactors.** Renames, field-number changes, oneof moves, enum changes, and streaming-mode changes can break clients.
2. **Designing schema around server implementation.** Common field bags, ORM-shaped messages, and reused request types make APIs harder to evolve.
3. **Skipping package versioning.** Stable published contracts need explicit versioned namespaces.
4. **Using enum zero values as real defaults.** Zero should usually mean unspecified/invalid so accidental omission does not look intentional.
5. **Choosing streaming too early.** Streaming changes infrastructure, load balancing, testing, and failure modes.
6. **Mapping every failure to `INTERNAL`.** Clients need meaningful, actionable status codes.
7. **Ignoring deadlines and cancellation.** This creates resource leaks and bad tail latency.
8. **Assuming gateway semantics match native gRPC.** HTTP/JSON paths, errors, metadata, streaming, and JSON types differ.
9. **Letting generated code drift.** Generation must be repeatable and checked.
10. **Logging payloads or metadata unsafely.** gRPC payloads often carry sensitive internal or customer data.

## Verification Checklist

- [ ] API ownership, consumers, stability, and exposure model are clear
- [ ] Package naming, versioning, and directory layout are consistent
- [ ] `.proto` style follows repo conventions or the documented default style guide
- [ ] RPC shapes are the simplest correct choice; streaming is justified where used
- [ ] Request/response messages are RPC-specific where evolution risk warrants it
- [ ] Field numbers are not reused; removals/deprecations are compatibility-safe
- [ ] Enums have safe zero values and unknown-value behavior is considered
- [ ] Optionality, validation, units, ID formats, and defaults are documented
- [ ] Buf/protoc generation is reproducible and checked in CI
- [ ] Breaking-change checks run against the correct baseline
- [ ] Canonical gRPC status codes and rich errors are mapped intentionally
- [ ] Auth, metadata, deadlines, cancellation, retries, and idempotency are designed and tested
- [ ] Gateway/Connect/gRPC-Web differences are documented when non-gRPC consumers exist
- [ ] Observability covers method/status/latency/message-size/stream signals without leaking sensitive data
- [ ] Runtime implementation was paired with the appropriate language skill
