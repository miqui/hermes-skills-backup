# UPSTREAM Decision Record — serverless-mcp

## Source

- **Repository**: https://github.com/serverless/serverless
- **Pinned commit**: `eb64c852316c112edcb7aafefa029544ea8c903d`
- **Source path**: `skills/serverless-mcp/`
- **Author**: Serverless Inc.
- **License**: Serverless Customer Agreement (repo LICENSE file is a URL to the agreement PDF; no standard OSS license in package.json)

## Artifact inventory

| File | Lines | SHA-256 |
|---|---|---|
| `SKILL.md` | 151 | `c7efa2ab01535bbf454cc907a0252e0e1de47c6b0f5d3e358d7d39ce53d98d58` |
| `references/config.md` | 462 | `022fe496f6384549665755e1227d2105c142f6f6c42c743efeb25dd7e5271b7c` |
| `references/server-code.md` | 239 | `330acb753514105e96c6fcdff0bac699019fd215b25195aaa1108f2b55ad93ec` |
| `references/testing.md` | 346 | `7d284e144593c6bbf4b7aaab0caf5a285e3529653d76e0f05fc44447b8f6d52a` |
| `references/troubleshooting.md` | 95 | `80ab7edd77610ac346d7b76f94f7659f26d152f43b45e1f5fd51856fe447b456` |

All files copied verbatim from upstream; byte-identical hashes confirmed.

## Normalization changes

1. **Frontmatter restructured**: moved `author` and license to top-level fields; preserved upstream `metadata.managed-by: serverless-framework` and renamed `metadata.version` to `metadata.upstream_version` to avoid collision with the Hermes-native `version` field.
2. **Hermes-native metadata added**: `metadata.hermes.tags`, `metadata.hermes.related_skills`, and structured `metadata.source` block (repo, commit, path, license, vendored flag).
3. **No content changes**: body text, code examples, and reference files are verbatim from upstream.

## Security review (OWASP AST10)

- **AST01 (Malicious Skills)**: No harmful instructions, data theft, or sabotage patterns found. PASS.
- **AST02 (Supply Chain)**: Pinned to exact commit SHA. No floating references. PASS.
- **AST03 (Over-Privileged)**: No filesystem, network, credential, or broad-permission instructions. Skill is purely educational/config guidance. PASS.
- **AST04 (Insecure Metadata)**: Name, description, and tags accurately reflect behavior. PASS.
- **AST05 (Unsafe Deserialization)**: No structured files loaded unsafely. No scripts or templates. PASS.
- **AST06 (Weak Isolation)**: No host-wide paths, blanket commands, or global assumptions. PASS.
- **AST07 (Update Drift)**: Pinned to immutable commit. Re-review trigger: any upstream revision update. PASS.
- **AST08 (Poor Scanning)**: Full-directory review of all 5 files completed. Betterleaks scan clean. PASS.
- **AST09 (No Governance)**: Owner: Miguel. Review cadence: on upstream revision update. PASS.
- **AST10 (Cross-Platform Reuse)**: No foreign agent ecosystem residue (no `allowed-tools`, no foreign registry references, no ecosystem-specific tool wrappers). PASS.

## Secret scan

- **Tool**: Betterleaks 1.7.3
- **Scope**: `/tmp/serverless-mcp-skill-search/skills/serverless-mcp/` (full upstream artifact)
- **Result**: `null` (no leaks found)
- **Exit code**: 0

## MCP spec version verification

The skill adheres to MCP protocol revision **2026-07-28** throughout:
- Elicitation uses `inputRequired({ inputRequests })` + `acceptedContent(...)` — not the deprecated push-style `elicitInput()`
- OAuth discovery follows RFC 9728
- Testing reference uses `mcp-protocol-version: 2026-07-28` headers and `io.modelcontextprotocol/protocolVersion` envelope
- Troubleshooting covers revision-specific capability negotiation

## Review state

- **Status**: Approved for installation
- **Reviewer**: Hermes Agent (automated review + user approval)
- **Owner**: Miguel
- **Re-review triggers**: any upstream revision update, any change to the `mcp:` config surface, any MCP spec version change

## Constraints

- Vendored snapshot — do not auto-update from upstream
- No live symlink to upstream
- Deployable examples referenced at `https://github.com/serverless/examples/tree/v4/mcp` are external links, not vendored content
