---
name: openapi-api-designer
description: Use when planning, designing, drafting, or refactoring HTTP REST API contracts as OpenAPI 3.2 documents, especially when business capabilities, resource boundaries, or AI-agent consumption quality matter.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [openapi, api-design, rest, oas, contract-first, ai-agents]
    related_skills: [openapi-specification, api-governance, writing-plans]
---

# OpenAPI API Designer

## Overview

Use this skill to design HTTP REST APIs as **OpenAPI 3.2.0** documents from product ideas, business capabilities, domain concepts, or rough endpoint requests. It is optimized for two audiences at once:

1. human developers who need a clear, implementable contract
2. AI agents and tool-using systems that need enough semantic context to choose and call operations correctly

The goal is not just to produce syntactically valid OpenAPI. The goal is to produce a spec that is structurally sound, navigable, semantically rich, and practical to implement. For specification mechanics, OAS 3.2+ syntax, validation, migration, componentization, references, and schema-level review, pair this skill with `openapi-specification`.

The authoritative syntax reference is the OpenAPI 3.2 specification:
- https://spec.openapis.org/oas/v3.2.0.html

When in doubt, prefer the specification and the local reference files over memory.

## When to Use

Use this skill when the user asks for any of the following, even if they do not say “OpenAPI” explicitly:

- design an API for a product idea or workflow
- draft a REST contract from business capabilities or domain nouns
- turn requirements, user stories, or resource ideas into endpoints and schemas
- refactor an existing API surface into a cleaner contract-first design
- create an API definition intended for SDK generation, MCP/tool use, or agent consumption
- modernize an existing OAS 3.0/3.1 spec into a more explicit OAS 3.2 shape

Do not use this skill for:

- AsyncAPI, GraphQL SDL, gRPC, or protobuf-only work
- pure implementation tasks where no contract design is needed
- lint-only or validation-only requests with no design work

## Inputs to Gather

Before drafting the spec, gather the minimum design inputs explicitly.

1. **Problem / API purpose**
   - What business outcome does the API enable?
   - What should clients be able to do?

2. **Business capabilities**
   - Stable things the business does, not UI screens or teams
   - These anchor resource boundaries and tag hierarchy
   - See `references/business-capability-mapping.md`

3. **Consumer profile**
   - Humans only, or humans plus AI agents/tooling?
   - If AI agents are consumers, apply the semantic-context checklist rigorously
   - See `references/semantic-context-for-ai.md`

4. **Style constraints**
   - Existing naming, versioning, auth, error, and pagination rules
   - If the user has no house style, use `references/rest-style-guide-default.md` and say so explicitly

5. **Expected output shape**
   - YAML by default
   - JSON only when explicitly requested
   - Single-file unless the API is large enough to justify a multi-document layout

If three or more of these are missing for a non-trivial API, pause and ask before writing the contract.

## Design Workflow

Follow this order. Capability framing should drive resource design, and resource design should drive operations and schemas.

### 1. Capture intent

Restate the API purpose and candidate business capabilities back to the user in short bullets before drafting paths.

This catches bad framing early, especially when the user names:
- screens instead of capabilities
- workflows instead of stable business outcomes
- technical layers instead of domain concepts

### 2. Map capabilities to resources

For each capability, identify the stable nouns it owns. Those nouns become resources.

Use these rules:
- a capability usually owns 1–5 core resources
- if one capability appears to own dozens of unrelated resources, it is probably multiple capabilities
- if two capabilities both “own” the same resource, stop and clarify ownership rather than silently guessing

Reflect the capability structure in top-level `tags` using OAS 3.2 hierarchy fields like `parent` and `kind`.

### 3. Define operations and schemas

For each resource:
- define collection and item operations only where they are justified
- reserve action-style endpoints for genuine business actions, not CRUD disguised as verbs
- move reusable shapes into `components.schemas`
- document parameters, request bodies, responses, and error shapes explicitly

Start from the local support files that actually exist in this skill directory:
- `assets/templates/openapi-skeleton.md`
- `assets/templates/pagination.md`
- `assets/templates/errors.md`
- `assets/templates/security-schemes.md`
- `assets/templates/common-parameters.md`
- `assets/examples/flights-api-excerpt.md`

Use `assets/examples/flights-api-excerpt.md` as the main worked example when you need a concrete model for resource paths, QUERY, streaming, tag hierarchy, or semantic richness.

### 4. Enrich for AI and tool consumers

This is the difference between a merely valid spec and a genuinely usable one.

Apply the checklist from `references/semantic-context-for-ai.md`. At minimum:
- every operation gets a short `summary`
- every operation gets a real `description`
- every operation gets a meaningful `operationId`
- every parameter and schema property gets a description
- every operation declares clear examples
- every operation declares capability and retry/side-effect hints where appropriate

Use only the controlled extension vocabulary documented in:
- `assets/extension-vocabulary.md`

Do not invent ad hoc `x-` keys unless you first extend that vocabulary file.

### 5. Validate and hand off

Before handing the spec back:
- validate that every `$ref` resolves and the document parses cleanly
- run the local lint guidance from `references/design-checklist.md`
- surface any remaining assumptions or unresolved trade-offs to the user
- save the output to the user-requested path, or to an agreed project-local path if one was provided during the task

When returning the result in chat:
- summarize capabilities, resources, auth model, and notable design choices
- mention any defaults you assumed
- if the spec is long, provide the file path instead of dumping the entire document inline

## OpenAPI 3.2 Features Worth Using Deliberately

These are the 3.2 features this skill should use on purpose when they improve clarity:

- root `$self` for canonical document identity in multi-file specs
- hierarchical tags via `parent` and `kind`
- `QUERY` for read-only searches that need structured bodies
- `querystring` parameter location for structured query grammars
- `itemSchema` for streaming payloads such as SSE and NDJSON
- response `summary`
- server `name`
- OAuth2 device authorization flow where CLI/device clients matter
- richer examples such as `dataValue` and `serializedValue` when wire format differs from logical value

Do not regress to older OAS 3.0-era patterns like:
- `nullable: true`
- schema-level singular `example` as the main documentation shape
- boolean `exclusiveMinimum` / `exclusiveMaximum`

See `references/oas-3.2-essentials.md` for concrete usage patterns.

## Output Conventions

- Prefer YAML unless the user explicitly asks for JSON
- Keep `openapi: 3.2.0` at the top
- Prefer a single file until scale or bounded-context separation clearly justifies splitting
- If you split files, make the entry document canonical and keep `$ref` boundaries intentional
- Put reusable pieces in `components` instead of scattering anonymous inline schemas
- Name operations in `verbResource[Qualifier]` camelCase style

## Reference Map

Read support files on demand rather than all at once.

- `references/oas-3.2-essentials.md` — what is materially new in OAS 3.2
- `references/business-capability-mapping.md` — capability discovery and resource ownership guidance
- `references/semantic-context-for-ai.md` — checklist for AI-usable contracts
- `references/rest-style-guide-default.md` — fallback style guide when the user has none
- `references/error-model.md` — problem-details guidance and standard error patterns
- `references/design-checklist.md` — final structural and semantic QA pass
- `assets/examples/flights-api-excerpt.md` — full worked example
- `assets/extension-vocabulary.md` — canonical `x-` extension vocabulary

## Common Pitfalls

1. **Designing around screens instead of capabilities**
   - “Booking Page” is not a capability.
   - Reframe around stable business outcomes and owned resources.

2. **Mirroring the database or ORM directly**
   - Avoid endpoints like `/users/{id}/update` or one-table-per-resource designs with no domain language.
   - Use HTTP methods properly and keep resource boundaries domain-driven.

3. **Using verbs everywhere**
   - The HTTP method already expresses most verbs.
   - Use action endpoints only for real business transitions like `/bookings/{bookingId}:cancel` or similar patterns the house style allows.

4. **Leaving schemas semantically empty**
   - A syntactically valid schema without property descriptions, examples, or error semantics is not enough for tool-using clients.

5. **Inventing extension vocabulary ad hoc**
   - Keep custom `x-` keys disciplined and documented in `assets/extension-vocabulary.md`.

6. **Referring to support files that do not exist locally**
   - This skill’s local support assets are Markdown reference/template files.
   - Do not point the user at nonexistent `.yaml` helper files.

7. **Overusing multi-file splits**
   - Splitting too early makes small APIs harder to review and validate.
   - Start single-file unless there is a clear bounded-context or size reason not to.

## Verification Checklist

- [ ] Frontmatter is Hermes-native and matches the local directory slug
- [ ] The contract reflects real business capabilities, not UI screens or team names
- [ ] Resource ownership is clear and consistent
- [ ] Every operation has `summary`, `description`, `operationId`, tags, and examples
- [ ] Error responses follow the local problem-details guidance
- [ ] Tag hierarchy uses OAS 3.2 navigation fields where appropriate
- [ ] Only documented `x-` extensions are used
- [ ] OAS 3.0 legacy patterns were not reintroduced
- [ ] The final file path or delivery method is explicitly stated to the user
- [ ] Any assumptions or default style-guide choices are disclosed in the handoff
