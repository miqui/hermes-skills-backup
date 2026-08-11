---
name: aws-mcp-setup
description: Use when checking or configuring Hermes access to AWS documentation or AWS MCP servers, including safe verification, transport selection, and MCP connectivity troubleshooting.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [aws, mcp, documentation, configuration, hermes]
    related_skills: [native-mcp, aws-agentic-ai, amazon-bedrock]
---

# AWS MCP Setup for Hermes

## Overview

Use this skill to safely inspect or configure AWS-related MCP servers in Hermes. It covers two distinct needs:

- **AWS documentation access** — search and read current AWS documentation.
- **AWS API access** — an explicitly configured, authenticated MCP server that exposes AWS actions.

Do not treat documentation access as permission to mutate AWS resources. Configuration and permissions remain separate decisions.

## Current-Profile Check

Start with a read-only inspection:

```bash
hermes mcp list
```

On this host, the `aws-docs` server is already enabled. Do not reconfigure or duplicate it unless it is unavailable or the user explicitly requests a change.

To test a configured server, use the Hermes MCP command appropriate to the installed version, such as:

```bash
hermes mcp test aws-docs
```

Do not print AWS credentials, environment files, or server headers while diagnosing configuration.

## When to Configure a Server

Configure an AWS MCP server only when all of the following are true:

1. The required capability is not already available through Hermes tools or an existing MCP server.
2. The user explicitly requests configuration or approves the proposed change.
3. The server's publisher, transport URL, package version, and permission model have been reviewed.
4. Required AWS access is least-privilege and scoped to the intended account, region, and actions.

Use `native-mcp` for Hermes-native `mcp_servers` configuration syntax and lifecycle behavior. Do not use Claude-specific `.claude.json`, `.mcp.json`, or `claude mcp` instructions in Hermes workflows.

## Safe Configuration Pattern

For a remote HTTP MCP server, use Hermes configuration with an explicit server name, URL, narrow timeouts, and only the headers strictly required. Store credentials outside committed configuration and avoid embedding long-lived secrets in a skill or chat transcript.

For a stdio MCP server, pin the server package/version after checking provenance and its published entry point. Do not use floating `@latest` packages for privileged AWS tooling.

Before enabling a server:

- Review the tool list and restrict exposure to the minimum necessary tools.
- Confirm whether the server can mutate infrastructure, read secrets, or invoke production APIs.
- Prefer a read-only environment/account for evaluation.
- Verify that access failures and logs redact credentials.

## Troubleshooting

| Symptom | Safe response |
|---|---|
| Server absent from `hermes mcp list` | Inspect Hermes configuration and confirm the user wants it added. |
| Connection fails | Check executable/URL reachability, package pin, TLS, and configured timeout; do not dump environment variables. |
| AWS access denied | Use a targeted, read-only AWS identity check and inspect the exact required action/resource; do not broaden to `*` by default. |
| Tools missing | Confirm the MCP server is enabled, restart Hermes if configuration changed, then inspect discovered tool names. |
| Credential concern | Report only `SET`/`UNSET`, verify source-of-truth and redaction controls, and never print token material. |

## Common Pitfalls

1. Copying MCP configuration intended for another agent client into Hermes.
2. Installing or executing floating third-party packages for privileged cloud access.
3. Equating an enabled documentation server with a configured AWS action server.
4. Placing AWS credentials in `mcp_servers` configuration, source files, terminal output, or skills.
5. Letting an MCP client's allowlist stand in for server-side authorization.

## Verification Checklist

- [ ] Existing MCP servers were checked with `hermes mcp list` before proposing changes.
- [ ] The user approved any configuration mutation.
- [ ] Publisher, URL/package version, transport, and permission model were reviewed.
- [ ] Credentials were verified only as presence state and remain outside source control.
- [ ] Tool exposure and AWS permissions are least-privilege.
- [ ] Hermes was restarted or a fresh session started when configuration changes require it.
