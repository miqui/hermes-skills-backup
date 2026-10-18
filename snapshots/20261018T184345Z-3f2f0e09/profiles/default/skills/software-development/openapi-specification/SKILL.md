---
name: openapi-specification
description: "Use when authoring, reviewing, validating, or migrating OpenAPI Specification documents constrained to OpenAPI 3.2.0 or newer. Focuses on spec syntax, document structure, JSON Schema alignment, components, references, examples, security schemes, validation, linting, and migration away from OAS 3.0/3.1 legacy patterns."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [openapi, oas, specification, api-contract, validation, json-schema, openapi-3-2]
    related_skills: [openapi-api-designer, api-governance, golang-openapi, requesting-code-review]
---

# OpenAPI Specification

## Overview

Use this skill for OpenAPI Specification work where the primary concern is the correctness, maintainability, and quality of the OpenAPI document itself. This is the specification-focused companion to `openapi-api-designer`.

The constraint is strict: author and recommend **OpenAPI 3.2.0 or newer only**. Do not emit new OAS 3.0 or 3.1 documents unless the task is explicitly to audit or migrate a legacy document. When migrating, the destination must be OAS 3.2+.

This skill is about the contract artifact: version line, document structure, paths, operations, components, schemas, references, examples, security schemes, extensions, validation, linting, and migration. For capability discovery, resource modeling, and product/API design decisions, pair with `openapi-api-designer`. For lifecycle checkpoints, publication governance, and enterprise review gates, pair with `api-governance`.

Authoritative reference:
- https://spec.openapis.org/oas/v3.2.0.html

## When to Use

Use this skill when the task involves:

- Writing an OpenAPI spec from an already-understood API shape.
- Reviewing an existing OpenAPI document for correctness and quality.
- Migrating OpenAPI 3.0 or 3.1 documents to 3.2+.
- Fixing schema, `$ref`, component, parameter, requestBody, response, example, or security scheme issues.
- Creating reusable `components` for schemas, responses, parameters, examples, headers, links, callbacks, path items, or media types.
- Validating an OpenAPI document before code generation, SDK generation, API review, publication, or tool/agent consumption.
- Deciding whether a construct should be inline or componentized.
- Applying OAS 3.2 features such as `$self`, hierarchical tags, `QUERY`, `querystring`, `itemSchema`, response `summary`, server `name`, OAuth2 device flow, and `components.mediaTypes`.

Do not use this skill as the only guide when:

- The user needs business capability discovery, resource modeling, or API product design; use `openapi-api-designer` too.
- The user needs governance, lifecycle, security review, publication controls, or audit artifacts; use `api-governance` too.
- The task is Go annotation mechanics with `swaggo/swag`; use `golang-openapi` too, then check whether the generated output can satisfy OAS 3.2+ expectations.
- The API is GraphQL, AsyncAPI, gRPC/protobuf, or event-contract-only work.

## Version Policy

### Required default

New or rewritten specs must use:

```yaml
openapi: 3.2.0
```

If a later 3.2+ version exists and the project explicitly requires it, use that version and verify against the relevant official spec. Otherwise, default to `3.2.0`.

### Legacy input handling

If given OAS 3.0 or 3.1 input:

1. Preserve the original file until the migration is verified.
2. Identify legacy constructs before changing the version line.
3. Migrate constructs to 3.2-compatible equivalents.
4. Validate the resulting OAS 3.2+ document.
5. Report behavior-impacting changes and any assumptions.

Never just change `openapi: 3.0.x` or `3.1.x` to `3.2.0` without checking legacy syntax.

## Minimum Document Shape

A useful OAS 3.2+ document should start with this shape:

```yaml
openapi: 3.2.0
$self: https://specs.example.com/example-api/v1/openapi.yaml
info:
  title: Example API
  summary: Example API contract
  description: |
    Human-readable purpose of the API, its audience, and any important boundaries.
  version: 1.0.0
  contact:
    name: API Support
    url: https://example.com/support
servers:
  - name: production
    url: https://api.example.com/v1
    description: Production environment.
tags:
  - name: examples
    summary: Examples
    description: Example operations.
    kind: nav
paths: {}
components:
  schemas: {}
  responses: {}
  parameters: {}
  examples: {}
  securitySchemes: {}
```

Use `$self` when the document has a canonical identity, is published separately from the API runtime URL, or participates in multi-document references. Omit it for tiny local drafts where no canonical URI exists yet.

## Authoring Workflow

### 1. Establish the artifact scope

Before editing, determine:

- Is this a new spec, review, repair, or migration?
- Is the output single-file or multi-file?
- Is YAML or JSON required? Prefer YAML by default.
- Which validators, linters, code generators, or gateways must consume it?
- Is the spec intended for humans, SDK generation, AI/tool consumers, or all three?

### 2. Validate the parse first

For existing specs, first check whether the file parses as YAML/JSON before making semantic edits. Parsing failures should be fixed before design improvements.

Common parse-level failures:

- indentation mistakes
- duplicate keys
- unquoted strings containing `:` where YAML interprets a mapping
- tabs in YAML indentation
- invalid `$ref` strings
- response status codes written as numbers instead of strings in YAML-sensitive contexts

### 3. Normalize the root object

Check the root object before paths:

- `openapi` is `3.2.0` or an explicitly accepted newer 3.2+ version.
- `info.title`, `info.version`, and useful `info.description` exist.
- `servers` have stable `name`, `url`, and `description` where environments are known.
- `tags` are declared before operations use them.
- `components` contains reusable definitions rather than repeated anonymous shapes.
- custom `x-` extensions are documented or intentionally project-standard.

### 4. Review paths and operations

For every path item and operation:

- Path template variables have matching `in: path` parameters with `required: true`.
- Every operation has a unique `operationId`.
- Every operation has `summary` and `description`.
- Every operation has at least one response.
- Request bodies are only used where HTTP semantics and tooling support are appropriate.
- Repeated response, parameter, and request shapes are componentized.
- Error responses use a consistent problem-details shape.

### 5. Review schemas as JSON Schema

OAS 3.2 builds on the JSON Schema alignment introduced in OAS 3.1. Treat schemas as JSON Schema 2020-12-style schemas unless project tooling imposes a documented constraint.

Check:

- Use `type: [string, "null"]`, not `nullable: true`.
- Use Schema Object `examples`, not schema-level singular `example`.
- Use numeric `exclusiveMinimum` / `exclusiveMaximum`, not booleans.
- Use `const`, `enum`, `oneOf`, `anyOf`, `allOf`, `not`, `dependentSchemas`, and `unevaluatedProperties` only when consumers support them.
- Add `title` and `description` to reusable schemas.
- Describe every property that external consumers must understand.
- Model binary or encoded values with `contentEncoding` and `contentMediaType` where appropriate.

### 6. Review examples

Examples are part of the contract.

Use:

- operation-level examples for requests and responses
- `components.examples` for reused examples
- realistic values rather than placeholders like `string` or `0`
- OAS 3.2 `dataValue` and `serializedValue` when the logical value differs from the wire representation
- multiple named examples for important variants, such as `minimal`, `full`, `validationError`, `notFound`, and `conflict`

### 7. Review security schemes

Check:

- `components.securitySchemes` declares every auth mechanism.
- Root `security` defines the default requirement.
- Public operations explicitly use `security: []`.
- OAuth scopes are documented in human-readable terms.
- OAuth2 device authorization flow is used when CLI/device clients need it.
- Deprecated flows or schemes are marked `deprecated: true` when applicable.
- Security documentation does not leak secrets or environment-specific credentials.

### 8. Validate, lint, and explain assumptions

Before handoff:

- Validate syntax and reference resolution.
- Lint style rules where a linter exists.
- Check for OAS 3.0 legacy constructs.
- Check operationId uniqueness.
- Check that examples match schemas where tooling supports it.
- State any assumptions, unsupported generator/tooling caveats, and follow-up risks.

## OAS 3.2+ Features to Prefer Deliberately

Use these when they clarify the contract:

| Feature | Use when |
|---|---|
| `$self` | Document needs canonical identity or stable reference base |
| Tag `summary`, `parent`, `kind` | API navigation benefits from hierarchy or grouping |
| `QUERY` operation | Read-only query requires a structured request body |
| `in: querystring` | The entire query string follows a custom grammar |
| `itemSchema` | Streaming response emits repeated structured items |
| response `summary` | Responses need short labels for docs or agent-facing UIs |
| server `name` | Environments need stable machine-readable identifiers |
| OAuth2 `deviceAuthorization` | Device/CLI clients need device-code flow |
| `components.mediaTypes` | Reusing schema/examples/encoding for media types |
| Example `dataValue` / `serializedValue` | Wire representation differs from logical value |

Do not use new features just to show novelty. Use them when they reduce ambiguity or improve tooling.

## Migration Checklist: OAS 3.0/3.1 to 3.2+

When modernizing a legacy spec:

- [ ] Change `openapi` only after syntax migration is planned.
- [ ] Replace `nullable: true` with JSON Schema union types such as `type: [string, "null"]`.
- [ ] Replace schema-level singular `example` with `examples` where appropriate.
- [ ] Replace boolean `exclusiveMinimum` / `exclusiveMaximum` with numeric thresholds.
- [ ] Review `$ref` siblings and composition behavior under JSON Schema alignment.
- [ ] Add server `name` values if multiple environments exist.
- [ ] Replace old tag grouping extensions with OAS 3.2 tag hierarchy where useful.
- [ ] Consider `components.mediaTypes` for repeated content definitions.
- [ ] Use response `summary` for important responses.
- [ ] Use `itemSchema` for SSE, JSONL, NDJSON, or JSON sequence streams.
- [ ] Validate all `$ref` targets after moving or componentizing schemas.
- [ ] Re-run downstream generator/tooling checks; not every ecosystem supports all OAS 3.2 features yet.

## Componentization Rules

Prefer components for anything reused or semantically important:

- Schemas used in multiple operations.
- Common errors and problem-details responses.
- Pagination parameters and response wrappers.
- Auth headers such as `Authorization`, `Idempotency-Key`, and `If-Match`.
- Reused examples.
- Shared media type definitions.
- Link definitions for follow-up operations.

Keep small one-off primitives inline when extracting them would reduce readability.

Name components by domain meaning, not implementation type:

```yaml
components:
  schemas:
    Booking:
      title: Booking
      description: A confirmed or pending travel booking.
```

Avoid names like `ResponseDto`, `Model1`, `Object`, or `ApiResult` unless they are real public concepts.

## Reference and Multi-File Guidance

For single-file specs, local references should usually look like:

```yaml
$ref: '#/components/schemas/Booking'
```

For multi-file specs:

- Keep an obvious entry document.
- Use `$self` for canonical document identity where publication URLs are stable.
- Keep references relative and predictable unless there is a strong reason for absolute URIs.
- Avoid circular reference structures that generators cannot handle.
- Validate from the entry document, not only individual fragments.
- Document the bundle command if downstream tools need bundled output.

## Validation Strategy

Use the project’s existing validation toolchain when present. If none exists, perform at least these checks:

1. YAML/JSON parses.
2. `openapi` is 3.2.0 or newer 3.2+.
3. Required root fields exist.
4. Every `$ref` resolves.
5. Every operationId is unique.
6. Path template variables and path parameters match.
7. Every operation has responses.
8. Legacy OAS 3.0 constructs are absent.
9. Security schemes referenced by operations exist.
10. Examples are realistic and schema-compatible where checkable.

If a local `openapi-api-designer` validation script is available for the active task, use it as a concrete validator. Otherwise, validate with the repository’s own tooling and report any tooling limitations.

## Review Checklist

For specification review, check:

- [ ] The file is valid YAML/JSON and has no duplicate keys.
- [ ] `openapi` is constrained to 3.2.0 or newer 3.2+.
- [ ] Root `info`, `servers`, `tags`, `paths`, and `components` are coherent.
- [ ] Every operation has unique `operationId`, `summary`, `description`, tags, and responses.
- [ ] Path parameters are declared correctly and match path templates.
- [ ] Request and response bodies use reusable schemas where appropriate.
- [ ] Error responses are consistent and reusable.
- [ ] JSON Schema syntax avoids legacy OAS 3.0 constructs.
- [ ] Examples are named, realistic, and attached at useful levels.
- [ ] Security schemes and operation security requirements are explicit.
- [ ] `$ref` boundaries are valid and maintainable.
- [ ] OAS 3.2 features are used when they clarify, not gratuitously.
- [ ] Downstream generator/tooling support is considered before using edge features.

## Common Pitfalls

1. **Bumping the version without migrating syntax.**
   `openapi: 3.2.0` does not magically fix legacy `nullable`, `example`, or boolean exclusivity patterns.

2. **Treating the spec as generated trash.**
   Even generated specs are contracts. Review names, descriptions, schemas, errors, and examples.

3. **Anonymous schemas everywhere.**
   Inline shapes make reuse, SDK generation, and review harder. Componentize meaningful models.

4. **Invalid path parameters.**
   Every `{id}` in a path needs a matching required path parameter, and every path parameter should correspond to a template variable.

5. **Duplicate or unstable operationIds.**
   SDKs and agents rely on operation IDs. They must be unique, stable, and meaningful.

6. **Examples that do not match schemas.**
   Bad examples train users and tools to call the API incorrectly.

7. **Overusing custom extensions.**
   Prefer standard OAS 3.2 fields first. If `x-` fields are needed, keep them documented and consistent.

8. **Ignoring generator support.**
   OAS 3.2 is the target, but downstream tools may lag. Surface compatibility risk instead of silently downgrading the spec.

9. **Confusing API design with spec mechanics.**
   If resource boundaries or business capabilities are unclear, pause and use `openapi-api-designer` rather than polishing a bad contract.

## Verification Checklist

- [ ] The output uses OpenAPI 3.2.0 or an explicitly accepted newer 3.2+ version.
- [ ] No new OAS 3.0/3.1-only patterns were introduced.
- [ ] The document parses and all `$ref` targets resolve.
- [ ] Operation IDs are unique and stable.
- [ ] Path parameters and templates match.
- [ ] Schemas use JSON Schema-aligned syntax and include useful descriptions.
- [ ] Examples are realistic and attached to operations, media types, or components.
- [ ] Security schemes and global/operation requirements are explicit.
- [ ] Validation/lint results are reported, including skipped checks and tooling limitations.
- [ ] Any migration assumptions, generator compatibility risks, or unresolved design issues are called out.
