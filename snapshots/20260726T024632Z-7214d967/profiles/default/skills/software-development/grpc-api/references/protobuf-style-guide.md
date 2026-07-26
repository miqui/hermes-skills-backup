# Protobuf Style Guide Notes

Source considered: Uber Protobuf Style Guide V2, `https://github.com/uber/prototool/blob/dev/style/README.md`.

Provenance: distilled on 2026-06-28 from the `dev` branch when `refs/heads/dev` resolved to commit `a6d064684c011c8482f4218c681a66a64031fb1d`. If using this guidance for strict governance, re-check the upstream file or pin an immutable blob URL for the exact revision under review.

Use this reference as a practical style influence for protobuf/gRPC API work, not as a mandate to copy every Uber/prototool rule. Prefer the repository's established style when it is consistent and enforced. For greenfield work with no house style, these defaults are strong starting points and map well to Buf lint/breaking workflows.

## Style Philosophy

- Optimize `.proto` files for API consumers and long-term compatibility, not server-side implementation convenience.
- Keep naming predictable across generated languages.
- Make packages versioned from the start for stable or published contracts.
- Prefer explicit deprecation and compatibility checks over "clean" rewrites that break generated clients.
- Treat documentation comments as part of the contract.

## Formatting and File Layout

Recommended defaults:

- Use two-space indentation.
- Use `proto3` for new definitions unless protobuf Editions is an established repo standard.
- Name files `lower_snake_case.proto`.
- Align directory structure with package name, such as `proto/acme/payments/v1/payment_service.proto` for `package acme.payments.v1`.
- Keep all files in one directory on the same package.
- Order file content as:
  1. license/header if applicable
  2. `syntax`
  3. `package`
  4. file options
  5. imports
  6. definitions
- Alphabetize file options and imports where practical.
- Use repo-root-relative imports from a consistent proto root.
- Avoid `public` and `weak` imports in normal API contracts.

## Package Naming and Versioning

Recommended defaults:

- Package segments should be short, descriptive, lowercase, and use only letters and digits where possible.
- Avoid underscores in package segments because generated code can become awkward in some languages.
- End stable packages with a major version such as `v1`, `v2`, etc.
- Use beta-style package versions, such as `v1beta1`, only when the organization has an explicit beta publication policy.
- Do not make breaking changes inside stable packages. Create a new package version instead.
- Stable packages should not depend on beta packages.

Avoid package sub-names that collide with language keywords, runtime packages, or misleading visibility concepts, such as `internal`, `public`, `private`, `protected`, and `std`. Also avoid top-level names that collide with target runtime packages, such as `grpc.*` in Python.

## Files: Service Files and Supporting Files

A useful convention is to separate:

- **Service files**: one service plus that service's RPC-specific request/response messages. Example: `payment_service.proto` containing `PaymentService`.
- **Supporting files**: reusable domain messages and enums. Example: `payment.proto` containing `Payment`, `PaymentStatus`, and related shared types.

For service files:

- Put the service definition near the top.
- Put request/response messages below the service.
- Order request/response messages to match RPC order.
- Prefer unique request and response message types per RPC.

Unique request/response messages intentionally create some duplication, but make future evolution safer. Reusing one request or response across multiple RPCs couples unrelated methods: adding or deprecating a field for one method can accidentally affect another.

## Naming Defaults

- Messages: `PascalCase`
- Services: `PascalCase`, commonly with a clear service suffix such as `PaymentService` or a house-standard suffix like `API`
- RPCs: `PascalCase`
- Fields: `lower_snake_case`
- Oneofs: `lower_snake_case`
- Enums: `PascalCase`
- Enum values: prefixed `UPPER_SNAKE_CASE`, such as `PAYMENT_STATUS_PENDING`

Avoid vague names like `common`, `data`, and `info` unless they have precise domain meaning. Prefer `id` over encoding implementation details like `uuid` unless the distinction matters to clients.

## Messages and Fields

- Messages should represent semantic domain concepts.
- Avoid "common fields" wrapper messages that exist only to reduce implementation duplication.
- Avoid single-field wrapper messages unless the wrapper has real domain/protocol meaning.
- Prefer copying a small number of common fields into semantically meaningful messages over creating meaningless containers.
- Document non-obvious field units, formats, validation, and default behavior.
- Do not use `json_name` unless the repository has a very deliberate interoperability reason.
- Avoid field names containing `descriptor`; generated Java code can collide.
- Prefer `filename` and `filepath` over `file_name` and `file_path` if following the Uber-derived convention.
- Timestamp fields should use `time` or end in `_time`.
- Duration fields should use `duration` or end in `_duration`.

## Enums

- Use enums for small, finite, relatively stable value sets instead of strings or integers.
- Do not use `allow_alias` in normal API contracts.
- Prefix enum values with the enum name to avoid protobuf/C++-style scoping collisions.
- Use a zero value that means unspecified/invalid, such as `PAYMENT_STATUS_UNSPECIFIED = 0`.
- If the domain has a deliberate unset state distinct from invalid/unspecified, add it as an explicit non-zero value and document it.
- Treat enum additions as compatibility-sensitive because older clients may not recognize new values.

## Nested Types

Nested messages and nested enums are allowed by protobuf but should be used sparingly.

Prefer top-level types when:

- The type might be referenced outside the containing message.
- The type has meaning independent of the containing message.
- The API is likely to evolve and reuse the type later.

Use nested types only when the nested type is truly local to one message for the lifetime of the API.

## Services and RPCs

- Services and RPCs should have comments with at least one complete sentence.
- Each service should have a clear bounded purpose.
- RPC comments should document intent, side effects, prerequisites, performance considerations, and retry/idempotency expectations where relevant.
- Prefer unique request and response messages per RPC.
- Keep RPC names verb-oriented and domain-specific.

Streaming RPCs should be treated as an explicit architecture decision, not a default. Unary RPCs plus pagination, polling, or chunked requests are often simpler to operate. Use streaming only when the API needs stream lifecycle semantics and the team can support flow control, long-lived connections, load balancing implications, cancellation, and resume/retry behavior.

## HTTP Annotations and Gateways

HTTP annotations, grpc-gateway, and transcoding are useful when HTTP/JSON consumers are real requirements, but they add a second semantic path to the API.

Before adding annotations, decide:

- Whether the HTTP resource shape is consumer-friendly or just RPC-over-HTTP.
- How gRPC status codes map to HTTP status and error bodies.
- Whether metadata/auth requirements remain clear.
- Whether streaming methods are supported, transformed, or omitted.
- Whether protobuf JSON mapping is acceptable for field names, enums, timestamps, and 64-bit integers.

If HTTP/JSON is a first-class product API, pair with `openapi-api-designer` and document the HTTP contract rather than treating gateway annotations as sufficient design.

## Deprecation, Reserved Fields, and Compatibility Caveat

Uber's prototool guide strongly favors `deprecated = true` over deleting definitions and using `reserved`, because deletion can break source compatibility for generated clients even when wire compatibility is preserved.

General Hermes guidance should be nuanced:

- For actively published generated-code APIs, prefer deprecating fields, enum values, messages, services, or methods before removal.
- If a field or enum value is actually removed, reserve both the field number and name to prevent unsafe reuse, especially if protobuf JSON is or may be used.
- Use Buf or repo-standard breaking-change checks to enforce the chosen policy.
- Do not reuse field numbers, enum numbers, JSON-visible names, or RPC signatures in stable packages.

## Documentation Comments

Use `//` comments above the thing being documented. Avoid inline comments and block comments in normal style.

Document:

- Messages, except trivial RPC request/response messages if the service/RPC docs already explain them.
- Enums and meaningful enum values.
- Services and RPCs.
- Fields with non-obvious semantics, defaults, units, validation, or authorization behavior.

Useful RPC documentation includes:

- What the RPC does and does not do.
- Side effects.
- Idempotency and retry safety.
- Preconditions and postconditions.
- Performance or payload-size considerations.
- Required metadata, auth, or tenant context.

## Buf Mapping

If using Buf instead of prototool, express the local style through:

- `buf format` for formatting.
- `buf lint` with a chosen profile plus local exceptions.
- `buf breaking` against the correct baseline.
- Review checklists for rules not encoded by lint.

Do not add a new lint rule only because it exists in a reference guide. Add it when the team accepts the rule and the repository can enforce it consistently.
