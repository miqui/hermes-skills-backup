# Security, Identity, and Credentials

## Inbound authentication

Choose one inbound Runtime authentication model for a given Runtime: IAM SigV4 or JWT/OAuth. Verify current AgentCore support and token requirements before implementation.

- **IAM SigV4** fits AWS-native workloads and role-based callers.
- **JWT/OAuth** fits browser, mobile, partner, or identity-provider-based callers.

Document issuer/discovery URL, audience, signing keys, token lifetime, scopes, tenant claims, error behavior, and key-rotation ownership. Never accept user-supplied identity claims without cryptographic validation.

## Outbound credentials

Use AgentCore Identity/Gateway credential mechanisms, Secrets Manager, or scoped workload roles instead of hard-coded client secrets. Store secret values outside source code, skills, images, logs, and chat content.

Safe checks report only presence/status, for example `SET`/`UNSET`; they never render secret values. Rotate a potentially exposed secret immediately rather than trying to sanitize downstream logs after the fact.

## Resource policies and cross-account access

Resource policies and IAM identity policies must both be reviewed. For every permission, define:

- principal/workload identity;
- exact action(s);
- exact resource ARN(s);
- intended account/organization/region boundary;
- conditions such as source account, source ARN, audience, tags, or VPC endpoint where applicable;
- the operational owner and revocation path.

Do not use a broad `*` action or principal as an expedient fix for `AccessDenied`. Diagnose the denied API/action/resource and make the smallest viable change.

## Gateway and MCP authorization

Gateway schemas and MCP tool descriptions are not authorization mechanisms. Validate agent-selected arguments, authenticate the caller, authorize the intended operation, and enforce tenant/resource boundaries in the target or a trusted gateway/proxy. Apply rate limits, audit logs, input size limits, and idempotency where relevant.

## Data protection

- Classify prompts, tool inputs/outputs, traces, artifacts, and evaluation datasets.
- Encrypt data in transit and at rest using managed or customer-managed keys as the workload requires.
- Configure log retention and access controls deliberately.
- Minimize sensitive payloads in traces; redact known secret fields at application/tool boundaries.
- Test unauthorized, cross-tenant, expired-token, and malformed-tool-call paths.

## Security review triggers

Re-review before deployment when changing a protocol, auth mode, identity provider, resource policy, IAM role, network path, external MCP server, credential provider, template, or package dependency.
