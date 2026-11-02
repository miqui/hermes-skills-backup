# BurgerAPI Reference

## Overview

BurgerAPI is a Bun-native backend framework centered around file-based routing, middleware, Zod validation, automatic OpenAPI generation, and built-in CLI-oriented project ergonomics.

Use BurgerAPI as a secondary framework reference for Bun backend work when the project benefits from convention-driven structure and framework-provided scaffolding. It is especially relevant when route discovery from files is a feature, not just an implementation detail.

This is a useful complement to Elysia, but not the default primary framework reference. Elysia is the stronger general-purpose Bun backend reference; BurgerAPI is the better reference when file-based routing and built-in scaffolding are central to the design.

## Canonical Docs

- Main site: https://burger-api.com/
- Docs intro: https://burger-api.com/docs/
- CLI Quick Start: https://burger-api.com/docs/getting-started/cli
- Tutorials: https://burger-api.com/docs/tutorials/intro
- Configuration: https://burger-api.com/docs/core/configuration
- API Routing: https://burger-api.com/docs/routing/api/static-routes
- Static Pages: https://burger-api.com/docs/routing/pages/static-pages
- Middleware: https://burger-api.com/docs/request-handling/middleware
- Schema Validation: https://burger-api.com/docs/request-handling/validation
- OpenAPI / Swagger: https://burger-api.com/docs/api/openapi
- Ecosystem: https://burger-api.com/docs/ecosystem/introduction

## Strengths

- File-based routing built into the framework model
- Good fit for convention-first project organization
- Zod-first validation workflow
- Automatic OpenAPI and Swagger support
- CLI-oriented onboarding and scaffolding
- Bun-native runtime positioning

## Mental Model

Think of BurgerAPI as a Bun-native framework where the filesystem is a major part of the application contract.

Typical emphasis:
- routes are discovered from folders and files
- middleware can be applied globally or to specific routes
- validation sits close to route definitions
- docs are generated from route metadata and schemas

This is appealing when you want the project tree itself to communicate the API shape.

## Recommended Project Fit

BurgerAPI is a good fit when:
- you want file-based API routing conventions
- a team values discoverability through directory structure
- you want CLI-assisted setup and framework conventions
- you want validation and docs tightly coupled to route files

It is less compelling when you want a more explicit code-first composition model with plugins as the main organizing concept. In that case, use Elysia as the primary reference.

## Key Patterns

### 1. Treat file structure as API structure

Because BurgerAPI leans on file-based routing, directory layout becomes part of the design. Keep route trees intentional and domain-driven rather than letting folders sprawl.

### 2. Keep route files focused

Even in file-based systems, route files should not become dumping grounds for all business logic. Move shared logic into domain services or utility modules.

### 3. Keep validation close to endpoints

BurgerAPI’s Zod-oriented validation model is strongest when schemas live near the routes that use them, unless a shared contract genuinely needs reuse.

### 4. Use generated docs as a contract check

If OpenAPI/Swagger is built from route metadata and schemas, review the generated docs regularly. They should describe the API you intend to expose, not just whatever the framework inferred.

### 5. Preserve convention clarity

File-based frameworks are easiest to maintain when naming conventions stay strict and predictable.

## Suggested Structure Guidance

If using BurgerAPI, document and keep consistent:
- where API routes live
- how dynamic segments are named
- where middleware belongs
- where validation schemas belong
- where shared business logic lives
- how docs metadata is attached to endpoints

## When to Choose BurgerAPI Over Elysia

Choose BurgerAPI when you want:
- file-based routing to be the primary organizing principle
- stronger convention-driven scaffolding
- route discovery from the filesystem
- framework-default docs and validation flow centered around route files

Choose Elysia when you want:
- a broader, code-first Bun backend reference
- plugin composition as the main app architecture tool
- a more general-purpose default for Bun services

## Common Pitfalls

1. Letting file-based routing become a substitute for actual architecture.
2. Packing business logic into route files because the filesystem already feels organized.
3. Allowing route naming conventions to drift across teams or modules.
4. Assuming generated OpenAPI output is automatically high quality without review.
5. Using BurgerAPI by default even when the project would be clearer with explicit code-first composition.

## Verification Checklist

- [ ] File-based routing is a deliberate project choice, not an accident
- [ ] Route files remain thin and readable
- [ ] Shared business logic lives outside route declarations
- [ ] Zod validation is close to the endpoints it protects
- [ ] Generated OpenAPI / Swagger is reviewed for correctness
- [ ] The team prefers convention-driven structure over a more explicit code-first model
