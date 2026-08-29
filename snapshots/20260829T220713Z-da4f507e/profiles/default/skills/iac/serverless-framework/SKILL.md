---
name: serverless-framework
description: "Serverless Framework v4 on AWS Lambda: config and MCP."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [serverless-framework, aws, lambda, mcp, typescript, packaging, iac]
    related_skills: [serverless-mcp, mcp-typescript-server, aws-serverless, aws-cdk, native-mcp]
---

# Serverless Framework (v4) on AWS Lambda

## Overview

Serverless Framework is a distinct deployment tool from AWS SAM and CDK —
it has its own `serverless.yml` schema, its own CLI (`serverless`/`sls`),
its own packaging/bundling behavior (esbuild-based zero-config bundling for
TypeScript), and — as of v4 — a **mandatory authentication requirement on
every CLI invocation**, including commands that make no AWS calls at all.

This skill covers the framework itself: config authoring, the native
MCP-server-on-Lambda integration, packaging pitfalls, and the auth gate.
For AWS-service-specific Lambda concerns (cold starts, concurrency, event
sources, SnapStart) that apply regardless of deployment tool, see
`aws-serverless`. For CDK/SAM equivalents, see `aws-cdk` / `aws-serverless`.

## When to Use

- Authoring or reviewing a `serverless.yml` (`frameworkVersion: '4'`)
- Deploying a Lambda function, HTTP API, or **MCP server** via Serverless
  Framework
- Debugging `serverless deploy`/`print`/`package` failures
- Building an MCP-on-Lambda POC or production service using the
  `mcp.servers` config key (pairs with `mcp-typescript-server` for the SDK
  side of the tool implementation)

## MCP-on-Lambda integration

Serverless Framework v4 has a native `mcp.servers.<name>.server` config key.
It points at a TypeScript module whose **default export** must be the
object `createMcpHandler(...)` returns (from `@modelcontextprotocol/server`
v2) — not the factory function, not a bare `McpServer` instance. Framework
auto-bundles the module with esbuild and generates the Lambda entry + HTTPS
route + response-streaming wiring.

For the deep, vendor-authored treatment of the MCP-on-Lambda surface —
config keys, server-code idioms for protocol revision 2026-07-28,
troubleshooting every `MCP_*` error, and deployment verification with
real round trips — see the dedicated `serverless-mcp` skill.

See `references/mcp-on-lambda.md` for:
- Minimal `serverless.yml` + `src/server.ts` + `package.json` starter trio
- Packaging rules (deps vs devDependencies, no prebuilt artifacts, uniform
  bundling across servers in one service)
- In-memory testing pattern (`InMemoryTransport.createLinkedPair()` +
  `@modelcontextprotocol/client`) that validates the exact factory
  `createMcpHandler` wraps, with zero AWS/network calls
- Auth/security caveats specific to MCP-on-Lambda (authorizer vs
  oauthDiscovery, WWW-Authenticate header remapping on REST API Gateway,
  Cognito DCR limitations, `state:` key rotation footgun)

## Critical pitfall — v4 CLI requires auth for EVERY command

`serverless print` and `serverless package` are the documented no-AWS-call
validation commands (render resolved config / build+stage the artifact
locally). But Serverless Framework v4 still hard-requires `serverless
login` or a license key before **any** CLI invocation runs — including
`print`, `package`, and even `--help` in some builds. Expect this exact
failure with no credentials configured, even for purely local validation:

```
✖ Error: You must sign in or use a license key with Serverless Framework
  V.4 and later versions. Please use "serverless login".
```

This is a genuine, current product constraint of Serverless Framework v4 —
not a broken install. Options, in order of typical preference:

1. `npx serverless login` — interactive, opens a browser OAuth flow
2. A license key referenced in `serverless.yml`:
   `licenseKey: ${ssm:/path/to/serverless-framework-license-key}` or
   `${vault:secret/serverless-framework/license-key}`
3. `SERVERLESS_ACCESS_KEY` env var (CI-style dashboard access token)

**If the task explicitly forbids creating credentials/accounts** (e.g. a
no-deploy POC constraint), you cannot actually execute `print`/`package` in
that environment. Do NOT skip validation silently — instead:
- Validate `serverless.yml` structurally with any locally available YAML
  parser (Python's `yaml.safe_load` via stdlib-adjacent PyYAML is a
  zero-extra-install fallback on most hosts) and assert the expected keys
  (`service`, `frameworkVersion`, `provider.runtime`, `mcp.servers.*.server`
  or `functions.*.handler`, etc.)
- Report plainly in your summary that `print`/`package` themselves could
  not be executed due to the CLI's auth requirement, and that the YAML
  check is a substitute, not equivalent, verification
- Never claim `serverless print`/`package` "passed" if the auth wall
  blocked them — this is an easy way to accidentally fabricate a
  verification result

## Packaging rules (general, not just MCP)

- Keep runtime deps (`@modelcontextprotocol/server`, `zod`, or any package
  your handler imports) in `dependencies`, not `devDependencies` — classic
  packaging strips `devDependencies`, causing `ERR_MODULE_NOT_FOUND` at
  Lambda cold start.
- `provider.runtime: nodejs20.x` (or higher) must be set explicitly for
  Node-based functions/MCP servers; an unset or non-Node runtime can
  silently default to a newer runtime (e.g. `nodejs24.x`) than intended.
- Config errors (bad runtime, name collisions, invalid keys) surface on
  *any* command that reads `serverless.yml` — `print` and `package`
  included, not just `deploy`. Use `print`/`package` as your pre-deploy
  gate specifically because they catch these without touching AWS.
- `serverless dev` (Dev Mode) does not serve MCP servers in current
  releases — there is no fully-local hot-reload loop for MCP; local
  validation realistically stops at build/typecheck/in-memory-client
  tests + `print`/`package`.

## Verification Checklist

- [ ] `serverless.yml` has `frameworkVersion: '4'` and a valid `provider.name`
- [ ] Runtime deps are in `dependencies`, not `devDependencies`
- [ ] For MCP servers: default export of the server module is
      `createMcpHandler(...)`'s return value, referenced correctly under
      `mcp.servers.<name>.server`
- [ ] `serverless print` / `serverless package` attempted; if blocked by
      the v4 auth wall, that blocker is reported explicitly (not silently
      substituted with an equivalent-sounding claim)
- [ ] No `serverless deploy` run unless deployment was explicitly
      requested and credentials/license are genuinely available
- [ ] In-memory MCP client tests (if applicable) exercise the same factory
      wrapped by `createMcpHandler`, not a duplicate/mocked copy

## Related Skills

- `mcp-typescript-server` — the MCP TypeScript SDK v2 API itself (tools,
  resources, prompts, transports) — use together when the Lambda function
  being deployed is an MCP server
- `aws-serverless` — AWS Lambda/API Gateway concerns independent of
  deployment tool (cold starts, concurrency, event sources)
- `aws-cdk` — the CDK equivalent deployment tool, for comparison
