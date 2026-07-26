---
name: typescript
description: "Use when editing, designing, reviewing, testing, migrating, or configuring TypeScript code and modules: type design, inference, generics, imports, factories, runtime schemas, control flow, test organization, tsconfig, and type-aware linting. Inspect repository conventions and compiler/runtime settings before applying repository-dependent rules."
version: 2.2.0
author: Epicenter conventions, Hermes-adapted
license: MIT
metadata:
  hermes:
    tags: [typescript, type-safety, generics, type-inference, factories, schemas, testing, code-review, migration, tsconfig, eslint]
    related_skills: [node-backend, bun-backend, test-driven-development, playwright-testing, aws-cdk, codebase-design]
---

# TypeScript Guidelines

## Overview

Use this skill to make TypeScript changes that preserve a clear source of truth, accurate inference, navigable APIs, and runtime-safe boundaries. It is intentionally useful across TypeScript repositories, while retaining the supplied Epicenter conventions as reference material.

**First inspect the target repository.** Apply framework-, compiler-, and package-specific rules only when its `tsconfig`, linting configuration, dependencies, or existing local conventions support them. Do not impose Svelte aliases, Arktype, TypeBox, `.js` import extensions, or ESNext iterator helpers on an unrelated project.

## When to Use

Use this skill when:

- Editing `.ts`, `.tsx`, `.mts`, or `.cts` modules.
- Defining, naming, deriving, moving, or reviewing types and public exports.
- Designing generic utilities, factory APIs, branded identifiers, discriminated unions, or runtime schemas.
- Reviewing casts, narrowing, error unions, serialization boundaries, and Go-to-Definition ergonomics.
- Organizing TypeScript tests and their relationship to source modules.
- Migrating a JavaScript codebase to TypeScript incrementally or selecting TypeScript compiler and type-aware linting configuration.

Do not use this skill as a replacement for framework-specific guidance. Pair it with `node-backend` or `bun-backend` for service/runtime work, `aws-cdk` for CDK code, and the repository's own test/tooling instructions for framework-specific tests.

## Operating Rules

### Establish the local constraints first

Before applying a convention, inspect:

1. `tsconfig*.json`, package metadata, and configured lint/format tools.
2. Existing nearby modules and the repository contribution guide.
3. Runtime-schema libraries and compiler targets already in use.
4. Whether the work is a public package boundary, a multi-implementation contract, or internal code.

For example, use `.js` in relative TypeScript imports only if the target module-resolution strategy requires it; use iterator helpers only when the configured target/lib and deployed runtime support them.

### Prefer a single source of truth

- Derive or import a type before declaring a new named shape.
- Treat local copies of upstream or runtime-owned shapes as boundary smells.
- Use `type`, rather than `interface`, when authoring new object types under these conventions.
- Keep explicit named types for true contracts: public APIs, protocols, discriminated result unions, capability ports, and shapes implemented by more than one runtime.
- Prefer `satisfies` when verifying conformance while preserving useful concrete inference.

### Keep public APIs navigable

- Export symbols at their declaration; reserve `export { ... } from ...` for barrel modules.
- Keep factory output types beside their factory and derive an exact factory handle with `ReturnType<typeof createThing>`.
- Put user-facing documentation and meaningful member annotations on the returned object surface.
- Avoid unnecessary wrappers, re-exports, destructure-re-exports, or hand-written return-shape aliases that make Go-to-Definition stop short of the source of truth.

### Make type safety reflect runtime reality

- Avoid `as any`; narrow with `unknown`, validation, brands, or precise helpers.
- Use a `Symbol` brand for factory identity; use real schema validation for untrusted boundary input.
- Prefer optional chaining for genuinely optional properties.
- Use predicate-style boolean names (`is`, `has`, `can`).
- Use exhaustive `switch` logic and `Record` mappings for closed domains where appropriate.
- Preserve identity fields across serialization/deserialization cycles; never hide a cross-system identity invariant with a silent fallback.

## Repository-Dependent Conventions

Adopt these when supported by the repository; otherwise follow its established alternatives:

| Convention | Apply when |
| --- | --- |
| `.js` in relative TypeScript imports | Node-aware ESM/module-preserve configuration requires explicit runtime extensions. |
| Absolute component imports / aliases | The project defines aliases such as `$lib` and uses them consistently. |
| Arktype optional-property syntax and inferred branded IDs | Arktype is installed and schemas are emitted to JSON Schema/OpenAPI/MCP boundaries. |
| `Symbol.for()` cross-package brands | Factory identity must survive package duplication or cross-module recognition. |
| Iterator `.toArray()` helpers | TypeScript lib and runtime support iterator helpers. |
| Source-shadowing `*.test.ts` files | The repository's test runner/layout follows colocated test conventions. |
| SCREAMING_SNAKE_CASE constant arrays | Existing project naming establishes this convention. |
| Zod schemas and `z.infer` | Zod is installed and selected for runtime/API/network boundaries; use it as an alternative to, not a replacement for, the repository's current schema library. |
| Strict `tsconfig` or type-aware ESLint templates | The project has reviewed compiler/runtime compatibility, installed the required packages, and wants these checks. |

## Reference Map

- [Project conventions](references/project-conventions.md): derivation, shape ownership, imports, exports, generics, destructuring, and factory return types.
- [Type safety and control flow](references/type-safety-and-control-flow.md): brands, casts, optional access, boolean names, exhaustive branches, error composition, and invariants.
- [Type organization](references/type-organization.md): co-location, extraction decisions, derived types, and option/constant patterns.
- [Factory patterns](references/factory-patterns.md): factory signatures and coupled-state extraction.
- [Runtime schema patterns](references/runtime-schema-patterns.md): runtime-validatable schemas and branded IDs.
- [Testing patterns](references/testing-patterns.md): single-use setup and colocated test layout.
- [Advanced TypeScript features](references/advanced-typescript-features.md): const generic inference and iterator helpers.
- [Advanced generics](references/advanced-generics.md): mapped and conditional types, `infer`, template literals, variadic tuples, utility types, and assertion functions.
- [Zod validation](references/zod-validation.md): Zod schema-first runtime validation and inferred types.
- [Result patterns](references/result-patterns.md): typed success/failure boundaries, intentional error subclasses, and safe public response transformations.
- [Migration and toolchain](references/migration-and-toolchain.md): incremental JS→TS migration, ESM migration, and repository-first configuration choices.
- [Strict bundler tsconfig template](templates/tsconfig.strict-bundler.jsonc): optional application baseline for an ESM-aware bundler.
- [ESLint flat-config template](templates/eslint.config.mjs): optional type-aware ESLint 9 baseline.

## Common Pitfalls

1. **Applying a project convention without checking project support.** Treat compiler settings, runtime targets, packages, and local style as evidence before enforcing an imported rule.
2. **Hand-writing a type already owned elsewhere.** Prefer inference, imports, or a deliberately named contract.
3. **Using casts to hide a boundary mismatch.** Fix the boundary, validate unknown input, or introduce a narrowly scoped brand/helper instead.
4. **Publishing factory types that duplicate the return object.** Keep the implementation as the source of truth when the factory owns the API.
5. **Treating an open external value as a closed union.** Exhaustiveness checks are for domains TypeScript actually proves are closed; untrusted inputs need runtime handling.
6. **Extracting trivial code into generic buckets.** Prefer co-location and apply the hop test before creating `types.ts`, `utils.ts`, or similar catch-alls.

## Verification Checklist

- [ ] Repository `tsconfig`, package/runtime target, and local conventions were inspected before applying conditional rules.
- [ ] New types are derived/imported where possible; explicit types represent real contracts.
- [ ] Public exports lead readers to the actual implementation or deliberate abstraction boundary.
- [ ] Untrusted runtime input is validated rather than trusted through a cast.
- [ ] Closed unions and finite mappings are exhaustive where a new variant should break the build.
- [ ] Tests cover changed runtime behavior and respect the repository's chosen test layout.
- [ ] Type checking, linting, formatting, and relevant tests were executed with the repository's documented commands.
