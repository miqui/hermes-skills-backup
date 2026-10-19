---
name: mcpjam-inspector
description: Use when interpreting or using mcpjam probe, doctor, OAuth, apps conformance, tools, resources, prompts, or Inspector UI output against MCP 2025-11-25; triage real protocol issues, interoperability warnings, implementation polish, scanner/client artifacts, and security-review findings with calibrated severity and confidence.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mcp, mcpjam, inspector, oauth, conformance, security-review, apps]
    related_skills: [native-mcp, secure-agent-skills]
---

# MCPJam Inspector

## Overview

Use this skill when analyzing MCP server behavior from `mcpjam` or MCP Inspector output. The goal is to separate:

- real protocol issues
- interoperability warnings
- implementation polish
- mcpjam or SDK artifacts

## When to Use

Use this skill when:

- interacting with an MCP server through the `mcpjam` CLI
- probing OAuth posture, authorization-server metadata, or dynamic registration behavior
- interpreting `mcpjam server probe`, `mcpjam server doctor`, `mcpjam server validate`, or `--debug-out` artifacts
- triaging MCP Apps metadata, `ui://` resources, or Inspector App Builder rendering
- deciding whether a scanner finding is real, overstated, or a client/SDK artifact
- performing an MCP server security review with calibrated compliance and security severities
- turning CLI evidence into an engineer-facing report with severity, confidence, and missing evidence

Do not use this as a substitute for configuring Hermes' native MCP client; use `native-mcp` for that.

## Prerequisites

- The `mcpjam` CLI is installed and available on `PATH`.
- The target MCP server URL, credentials, or token source is known when authenticated inspection is required.
- For browser/UI rendering, Inspector App Builder must be available locally or launchable through `mcpjam`.

## Interactive use

When the user wants to connect to a server and use it:

1. Probe the server first: `mcpjam server probe --url <url> --quiet --format json`.
  - Use the probe to learn auth posture, resource metadata, authorization-server metadata, and registration strategies before assuming the connected surface is public.
2. If the probe shows `oauth_required`, authenticate with `mcpjam oauth login --credentials-out <path>` or run `mcpjam oauth conformance --credentials-out <path>` when the task is specifically to test the OAuth flow.
3. Discover tools: `mcpjam tools list --url <url> --credentials-file <path> --quiet --format json`.
  - Tools with `_meta.ui.resourceUri`, deprecated `_meta["ui/resourceUri"]`, or `openai/outputTemplate` in `toolsMetadata` have interactive UI.
  - For a specific tool, check `toolsMetadata.<toolName>._meta.ui.resourceUri`, `toolsMetadata.<toolName>._meta["ui/resourceUri"]`, or `toolsMetadata.<toolName>["openai/outputTemplate"]`.
4. Execute a tool: `mcpjam tools call --url <url> --tool-name <name> --tool-args <json> --credentials-file <path>`.
5. Execute with UI: `mcpjam tools call --url <url> --tool-name <name> --tool-args <json> --credentials-file <path> --ui`.
  - `--ui` starts or attaches to the local Inspector backend and renders the completed result in App Builder.
  - In non-TTY, agent, and CI runs, `--ui` does not open a browser by default. Pass `--open` when the CLI should open App Builder itself.
  - `--open` opens a system browser URL; it does not attach an already-controlled automation browser or make fresh tabs hydrate an injected render. Use `--no-open` when browser automation already opened Inspector App Builder. Use `--attach-only` when startup, browser opening, and discovery must all be disallowed.
  - `no_active_client` means the Inspector backend may be running but no browser client is attached. If manual recovery is needed, use `mcpjam inspector open`, not `mcpjam inspector start`.
  - `unknown_server` in the root `error.code` or an `inspectorRender.commands.*.error.code` means Inspector could not match the requested server. If the message says App Builder is focused on another server, retry with `--server-name <focused-name>`.
  - Treat UI success as `inspectorRender.status === "rendered"`, not exit code `0` alone. If the render is `skipped`, branch on `inspectorRender.remediation` or the stable root `warning.code`.
  - Use `--require-render` when the UI render itself is the deliverable and a skipped render should fail the command.
  - Do not require external screenshots as proof of render success; iframe/canvas content can defeat browser snapshot tools. Prefer `inspectorRender.status`, command responses, and snapshot evidence.
  - Use `--ui` only when the tool has UI metadata or the user explicitly asks to see UI.

When the user asks to investigate, audit, or triage, use the Investigation workflow below.

## Default stance

- Treat raw request/response evidence as higher trust than normalized CLI convenience output.
- Separate observations, compliance issues, and security findings. They are related, but not interchangeable.
- Map claims to spec strength: `MUST` and `MUST NOT` are strong conformance signals; `SHOULD` and `RECOMMENDED` are softer guidance; `MAY` and optional fields are usually informational.
- Do not label a security finding `high` unless you can support a concrete attacker benefit or clear breakage path.
- When evidence is ambiguous, lower confidence or use `pending` before overstating the conclusion.

## Investigation workflow

1. Start with the narrowest command that actually proves the claim.
2. If the command may fail, you want a reusable handoff artifact, or CI should retain evidence, add `--debug-out <path>` to `mcpjam server probe`, `mcpjam server validate`, `mcpjam tools call`, or `mcpjam oauth login`.
3. If the probe shows `oauth_required` and the task is to inspect the server surface, continue with `mcpjam oauth login` or another supported auth flow to obtain reusable credentials before judging post-auth behavior. For multi-command connected sessions, use `--credentials-out <path>` on `mcpjam oauth login`, `mcpjam oauth conformance`, or `mcpjam oauth conformance-suite` to persist tokens and `--credentials-file <path>` on later commands; use the command-specific caveats in this skill for access-token-only exceptions. When a token is already available (CI, M2M, env var), prefer a credentials file when possible and pass `--access-token` or `--oauth-access-token` only as an escape hatch.
4. After successful auth, inspect the connected surface with direct commands such as `mcpjam server info`, `mcpjam server capabilities`, `mcpjam tools list`, `mcpjam resources list/read/templates`, and `prompts list/get`.
5. Use `mcpjam server doctor --out <path>` when you need one breadth-first snapshot instead of several single-purpose command outputs.
6. If the output came from `mcpjam server doctor` or a `--debug-out` artifact, split it into primary command evidence, probe evidence, and connected-sweep evidence.
7. If the claim is specifically about MCP Apps tool metadata or `ui://` resources, start with `mcpjam apps conformance --quiet --format json` before dropping to `mcpjam tools list` or `mcpjam resources read`.
8. If the claim is about a tool result rendering in Inspector, use `mcpjam tools call --tool-name <name> --tool-args <json|@file|-> --ui --quiet --format json`.
  - In non-TTY runs, add `--open` if no Inspector browser client is already attached.
  - If browser automation already opened `http://127.0.0.1:6274/#app-builder`, add `--no-open`; `--open` launches a system browser and may not target the automation-controlled client.
  - Confirm UI delivery with `inspectorRender.status === "rendered"`. Treat `inspectorRender.remediation` and stable skipped-render `warning.code` values as recovery hints, not MCP tool failures.
  - If `unknown_server` appears in the root error or command errors and the message names the focused server, retry with `--server-name <focused-name>`.
  - Use `--require-render` when a skipped render should become a hard error instead of a warning.
9. If a field may be CLI-added or SDK-normalized, check the command-specific caveats, hard rules, and raw evidence before concluding anything.
10. If the claim depends on MCP semantics, verify it against the MCP 2025-11-25 specification before finalizing the conclusion.
11. If the task involves security review, follow the security review workflow below and consult MCP security best practices when additional checklist depth is needed.
12. Write the result using the output contract below.

## Security review workflow

Use this when the task is to assess an MCP server's security posture. All checks use existing CLI commands. No special security tooling is needed. Do not assume every server should require auth.

### Phase 1: Observe (read-only)

Run `mcpjam server probe --url <target> --quiet --format json` first. Add `mcpjam oauth metadata` or `mcpjam server doctor --out <path>` only when they clarify the picture.

- Record an initial auth signal:
  - `full-auth candidate`: probe `status` is `oauth_required`
  - `public-or-mixed candidate`: probe `status` is `ready`
  - `unknown`: probe is only `reachable`, `error`, or otherwise ambiguous
- Capture discovery facts:
  - OAuth metadata URLs and whether they point to public, private, or suspicious targets
  - `scopes_supported`, `WWW-Authenticate`, and PKCE methods
  - registration strategies such as `dcr`, `cimd`, and `preregistered`
- Record the evidence surface you are trusting. Raw probe/RPC evidence beats doctor summaries or convenience fields.
- Phase 1 can produce observations and compliance notes. By itself it should not produce a `high` security severity.

### Phase 2: Provoke (behavior, still mostly unauth)

Treat the Phase 1 auth signal as provisional until behavior confirms it.

- For a `full-auth candidate`:
  - run DCR shape probes if DCR is supported
  - spot-check representative unauth `mcpjam tools list` or `mcpjam tools call` behavior when feasible
  - check malformed, expired, or obviously wrong-audience token handling without overstating what a rejection proves
- For a `public-or-mixed candidate`:
  - run unauth `mcpjam tools list`
  - classify exposed tools as read-only, write, or side-effect
  - call representative public tools unauth
  - check whether gated tools fail with a clean auth challenge instead of silent empty data or partial data
- Anonymous tiers, rate limits, or degraded public access are posture notes, not a separate posture class.
- Reclassify to one of `no-auth`, `full-auth`, `mixed-auth`, or `unknown` once Phase 2 behavior is clear. If Phase 2 contradicts Phase 1, update the posture and rerun the relevant checks instead of forcing the old classification.
- Input-validation hits from Phase 2 cap at `medium` security severity until Phase 3 proves attacker benefit.
- Design or posture findings can be real security findings in Phase 2, but do not auto-promote them. Document the unsafe behavior, abuse path, and any owner-intent uncertainty before calling them `medium` or `high`.

### Phase 3: Exploit or confirm attacker benefit

Use `mcpjam oauth login` and the same browser session when the proof depends on consent or cookies.

- Use Phase 3 to turn a plausible concern into a real end-to-end security finding:
  - DCR plus authorization flow proof
  - redirect URI exact-match bypass proof
  - foreign-token acceptance or token passthrough proof
  - code, token, or cross-tenant data capture
- Consent skip is one route to `high`, not the only route. Any demonstrated chain that shows concrete attacker gain can justify `high`.

### Phase 4: Inventory blast radius

- After auth succeeds, decode JWT claims, inspect `Mcp-Session-Id` with raw logs, and enumerate tools, resources, prompts, scopes, and tenant context.
- Phase 4 is mainly blast-radius calibration. Treat it as context unless you also prove abuse.

### Security severity calibration

- `high`: demonstrated attacker benefit or conforming-client breakage with direct evidence
- `medium`: credible security issue with a concrete attack scenario, but end-to-end proof is still partial
- `low`: hardening gap or limited-impact security concern
- `pending`: plausible security concern with a specific missing proof step that could materially raise or lower severity
- `info`: true observation with no credible attacker benefit yet

Use `pending` instead of manufacturing a `medium` or `high` security severity from a checklist hit.

## Command choice

- `mcpjam server probe`: HTTP transport reachability, initialize behavior, and OAuth discovery hints.
- `mcpjam server doctor`: combined triage artifact for probe plus connected behavior. Good for breadth, not always sufficient to prove wire-level behavior by itself.
- `mcpjam oauth metadata`, `mcpjam oauth proxy`, `mcpjam oauth debug-proxy`: exact endpoint and metadata inspection when conformance output looks surprising.
- `mcpjam oauth login`: obtain reusable credentials and verify the authenticated MCP path. Use `--credentials-out <path>` to save tokens to disk (mode 0600) so later connected commands can use `--credentials-file <path>` without manual token extraction; check the relevant command behavior for cases that require a non-expired access token. Use this when the goal is to inspect a server that requires OAuth, then follow it with connected commands rather than stopping at the login result.
- `mcpjam oauth conformance`, `mcpjam oauth conformance-suite`: flow-level auth checks. Treat these as targeted probes, not a complete security review. Use `--credentials-out <path>` when a passing flow should hand credentials to later connected commands; use `--credentials-file <path>` after that instead of extracting tokens from JSON output. Raw JSON output redacts OAuth secrets by default. When `--conformance-checks` is enabled, the command can directly probe DCR non-loopback `http://` redirects, invalid client rejection, authorization-endpoint redirect mismatch handling, invalid bearer-token rejection at the MCP server, and token-endpoint redirect mismatch handling.
- `mcpjam apps conformance`: server-side MCP Apps checks for `_meta.ui.resourceUri`, `ui://` resources, `resources/read`, HTML MIME and payload shape, and `_meta.ui` metadata. Use this for MCP Apps surface triage.
- `mcpjam server info`, `mcpjam server capabilities`, `mcpjam server validate`, `mcpjam server ping`, `mcpjam server export`: connected behavior after initialization and auth.
- `mcpjam tools list` and `mcpjam tools call`, `mcpjam resources list/read/templates`, `mcpjam prompts list/get/list-multi`: direct post-connect capability checks. With `--ui`, `mcpjam tools call` renders the completed tool result in Inspector and reports `inspectorRender` as UI command/render evidence.
- Prefer `--quiet --format json`. Add `--rpc` when available if you need request and response evidence rather than a summary. Add `--debug-out` when you need a failure-safe artifact, not as a replacement for raw evidence.
- Use `--reporter junit-xml` or `--reporter json-summary` for CI report artifacts on conformance and diff commands. `mcpjam server validate` does not accept `--reporter`; use `--debug-out` for validation artifacts. Do not use `--format junit-xml`; `--format` is only for raw `json` or `human` output.
- For JSON-valued options, prefer `@path` or `-` stdin over shell-escaped inline JSON when payloads are generated or contain quotes. For example: `mcpjam tools call --url <target> --tool-name <name> --tool-args @params.json --quiet --format json`.

## Output contract

### General triage output

For non-security tasks, return:

- `Verdict`: `real issue`, `interop warning`, `implementation polish`, or `scanner/client artifact`
- `Severity`: `high`, `medium`, `low`, or `info`
- `Confidence`: `high`, `medium`, or `low`
- `Why it matters`: one short paragraph tied to interoperability, security, or user impact
- `Evidence`: the exact CLI behavior that supports the claim
- `Missing evidence`: what would need to be confirmed before raising severity or confidence

### Security review output

For each claimed security-review finding, return:

- `Verdict`: `real issue`, `interop warning`, `implementation polish`, or `scanner/client artifact`
- `Compliance severity`: `high`, `medium`, `low`, or `info`
- `Security severity`: `high`, `medium`, `low`, `info`, or `pending`
- `Confidence`: `high`, `medium`, or `low`
- `Attack scenario or pending rationale`: if `Security severity` is `medium` or `high`, open with 2-3 sentences answering who the attacker is, what they need, and what they gain; if it is `pending`, say exactly what proof is missing
- `Verified via`: the phase plus exact command or result that supports the claim
- `Evidence`: the exact CLI behavior that supports the claim
- `Missing evidence`: what would need to be confirmed before raising severity or confidence

## Hard rules

- Never call `toolsMetadata` an MCP server field.
- Never use removed app/widget commands for UI rendering. Use `mcpjam tools call --ui`; use `mcpjam resources read --resource-uri ui://...` for raw resource HTML.
- Never manually orchestrate Inspector API calls when `mcpjam tools call --ui` can drive the render.
- Never skip `mcpjam tools list` discovery when the user names a server but not a specific tool.
- Never infer prompt support from an empty prompts list unless you have raw RPC evidence that `prompts/list` was actually sent and answered by the server.
- Never stop at `oauth_required` when the user asked to inspect the authenticated server surface and the CLI can complete login. Authenticate and continue with post-login commands when feasible.
- Never treat a passing `mcpjam apps conformance` result as full SEP-1865 conformance. The current command is server-side only and does not prove host lifecycle, sandbox proxy, or postMessage bridge behavior.
- Never treat missing optional metadata such as `outputSchema`, content annotations, `scopes_supported`, or `scope` hints as a hard failure without a `MUST`.
- Separate OAuth RFC violations from MCP profile preferences.
- Distinguish "the server correctly rejected a bad request" from "the overall design is secure."
- Treat `--debug-out` artifacts as aggregated evidence envelopes, not pure wire captures.
- Never flag missing `scopes_supported` or missing `scope` in `WWW-Authenticate` as a security issue. Both are optional.
- Never claim a server is "secure" based solely on it rejecting one specific bad input. A single negative test does not prove broader security posture.
- Never treat a passing `oauth_invalid_token` or redirect-mismatch probe as proof that the whole authorization design is secure. Those checks only prove the exact case that was sent.
- Never let a checklist hit assign `high` security severity by itself.
- JWT `aud` mismatch is not token passthrough proof unless you show the server accepts a token issued for a different audience or resource, or otherwise misbinds the token.
- Supporting `plain` PKCE is usually hardening only. It cannot compound with attacker-owned-client DCR flows where the attacker chose the verifier.
- Hostile `redirect_uri` values are not SSRF unless you show the server fetches them.
- Public unauthenticated access is not itself a finding. Check whether behavior matches advertised posture and whether exposed surfaces are safe by design.
- Anonymous trial or rate-limited access is a posture note, not a separate severity finding.
- When compounding findings, explain the compound attack path. Do not just list unrelated findings and call the combination worse.

## Reference map

This local skill is intentionally self-contained; do not assume additional `references/*.md` files exist unless they are added later. Use these sections as the local reference map:

- **Command-specific caveats:** `Command choice`, `Interactive use`, and `Hard rules`. Use these for artifact shapes, UI-rendering behavior, credentials-file handling, local enrichments, merged errors, and normalized empty arrays.
- **MCP 2025-11-25 interpretation:** `Default stance`, `Investigation workflow`, and `Hard rules`. Verify any normative claim against the MCP 2025-11-25 specification before raising severity.
- **Security best practices:** `Security review workflow` and `Security severity calibration`, plus the MCP security best practices source at https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices when deeper checklist coverage is required.
