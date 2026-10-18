---
name: aws-agentic-ai
description: Use when designing, deploying, securing, operating, or troubleshooting Amazon Bedrock AgentCore Runtime, Gateway, Memory, Identity, Code Interpreter, Browser, Observability, Agent Registry, or Evaluations.
version: 1.0.1
license: MIT
metadata:
  hermes:
    tags: [aws, bedrock-agentcore, agentic-ai, runtime, gateway, mcp, identity, observability]
    related_skills: [amazon-bedrock, aws-cdk, aws-iam, aws-observability, native-mcp, aws-mcp-setup]
---

# AWS Bedrock AgentCore

## Overview

Use this skill for **Amazon Bedrock AgentCore** service design and operations: agent hosting, MCP gateways, memory, OAuth/identity, isolated browser and code execution, telemetry, registry, and evaluations. It is an AgentCore-focused companion to `amazon-bedrock`, which remains the primary skill for foundation-model invocation, Knowledge Bases, Guardrails, and Bedrock Agents.

The source package was supplied locally and normalized for Hermes. Its original examples are treated as implementation patterns—not as timeless API truth. AgentCore evolves quickly; verify service APIs, supported regions, SDK/CLI parameters, model IDs, and protocol versions against current AWS documentation before acting.

## When to Use

- Deploying or operating an AgentCore Runtime using HTTP, MCP, A2A, or AG-UI.
- Designing Gateway tools, OAuth flows, credential providers, or runtime authorization.
- Choosing between AgentCore Memory, S3-backed state, or per-session filesystem state.
- Instrumenting AgentCore workloads with OpenTelemetry, CloudWatch, or X-Ray.
- Building Agent Registry or Evaluations workflows.
- Reviewing AgentCore resource policies, cross-account access, or secret-handling patterns.
- Adding AgentCore capabilities to Strands, FastAPI, Claude Agent SDK, or similar frameworks.

Do **not** use this skill for general Bedrock model selection, RAG/Knowledge Bases, Guardrails, or generic AWS infrastructure when `amazon-bedrock`, `aws-cdk`, `aws-iam`, or another focused skill is a better match.

## Operating Principles

1. **Confirm the service boundary first.** Runtime hosts agents/tools; Gateway exposes tools; Identity governs inbound/outbound credentials; Memory persists context; Registry catalogs resources; Evaluations scores trace data.
2. **Select one Runtime protocol deliberately.** HTTP is application-defined; MCP exposes tools/data; A2A supports agent-to-agent collaboration; AG-UI streams standardized frontend events. One Runtime uses one protocol configuration.
3. **Use CDK for production deployments.** Treat starter/CLI deployment workflows as prototypes unless the complete peripheral infrastructure, IAM, observability, and rollout controls are managed elsewhere.
4. **Start read-only.** Inspect account, region, existing resources, IAM boundaries, quotas, and current docs before any create/update/delete action.
5. **Keep credentials outside prompts and source control.** Use AgentCore Identity, Gateway credential providers, Secrets Manager, or scoped IAM roles. Never print secrets to validate them.
6. **Validate before deployment.** Run local/unit/static checks, image and architecture checks, CDK synth/diff, and least-privilege review. Do not use an unattended deploy command as a default.
7. **Record the decision.** Capture protocol, region, auth mode, deployment ownership, data classification, and rollback strategy.

## Workflow

### 1. Scope and discover

- Confirm target AWS account and region without disclosing credentials.
- Identify the desired service(s), callers, data sensitivity, and whether the action is read-only, provisioning, or destructive.
- Check current AWS documentation and the applicable reference in this skill before relying on source examples.

### 2. Choose runtime and state patterns

Use `references/runtime-and-protocols.md` for the container contract, protocol selection, sessions, and lifecycle trade-offs.

- Prefer **HTTP** for custom request/response contracts.
- Prefer **MCP** when exposing reusable tools or data capabilities.
- Prefer **A2A** for independently implemented agents that collaborate as opaque peers.
- Prefer **AG-UI** for a rich agent-to-frontend event stream.
- Use externalized Memory/S3 state when portability matters; only rely on in-process session affinity when the deployment is intentionally AgentCore-specific.

### 3. Design security and authorization

Read `references/security-identity-and-credentials.md` before configuring JWT, OAuth, service credentials, or resource policies.

- Choose one inbound Runtime auth mode: IAM SigV4 **or** JWT/OAuth.
- Use least-privilege roles and exact resource ARNs; require explicit denial/allow reasoning for resource policies.
- Keep third-party OAuth token handling in Identity/Gateway flows where possible.
- Treat user-controlled input and LLM-selected tool arguments as untrusted; validate them at tool and downstream service boundaries.

### 4. Build and validate

Use `references/deployment-and-operations.md` and the reviewed templates in `templates/`.

- Runtime containers must meet the selected protocol's port/endpoint contract, run as non-root, and support ARM64 when using a container artifact.
- Use a multi-stage build with locked dependencies; scan images and validate the application locally.
- For production, use CDK with explicit IAM, network, logging, secrets, and version/endpoint controls.
- Treat every supplied template as a starting point. Confirm current package APIs and generated CloudFormation/SDK shapes before deployment.

### 5. Observe, evaluate, and operate

- Enable OpenTelemetry-compatible tracing, structured logs, and relevant CloudWatch alarms.
- Review traces and tool calls with data minimization; do not log credentials or sensitive user data unnecessarily.
- Use Evaluations only after trace collection and data-retention controls are understood.
- Use the Registry for governed discovery, with explicit record ownership and approval workflow.

## References

- `references/runtime-and-protocols.md` — Runtime contract, sessions, protocols, lifecycle, tool integration, and persistence.
- `references/deployment-and-operations.md` — CDK deployment, network/auth architecture, observability, and framework choices.
- `references/security-identity-and-credentials.md` — OAuth, credential isolation, resource policies, cross-account access, and secret safety.
- `references/services-registry-and-evaluations.md` — Gateway, Memory, Browser, Code Interpreter, Registry, Evaluations, and governance.
- `references/import-review-and-source-map.md` — Imported-source inventory, normalization decisions, and re-review triggers.

## Templates

Templates are deliberately stored under `templates/`, not as executable automation. Review, adapt, and validate them for the target account/region and current SDK before use.

- `templates/runtime-dockerfile.md`
- `templates/runtime-fastapi-template.py`
- `templates/mcp-server-template.py`
- `templates/a2a-server-template.py`
- `templates/agui-server-template.py`
- `templates/gateway-custom-resource-lambda.py`
- `templates/gateway-deploy-template.sh`
- `templates/gateway-validate-deployment.sh`

## AWS MCP Documentation Access

Load `aws-mcp-setup` only when AWS documentation MCP connectivity needs verification or configuration. The current Hermes profile already lists an enabled `aws-docs` MCP server; do not alter MCP configuration merely because this skill is loaded.

## Common Pitfalls

1. Treating an example command, SDK call, model ID, port, or quota as current without checking the official documentation.
2. Combining incompatible Runtime protocols or inbound authentication modes on the same Runtime.
3. Using direct container/session memory as durable state without a recovery plan.
4. Putting tokens, API keys, or secrets in source, prompts, generated templates, logs, or CLI output.
5. Deploying production resources from a starter-toolkit or shell template without CDK review, IAM scoping, and a rollback plan.
6. Treating client-side MCP filtering as authorization; enforce sensitive permissions in Gateway, an authenticated proxy, the MCP server, or its backend.
7. Assuming a supplied custom-resource template matches the installed AWS SDK without validating its API request/response model.

## Verification Checklist

- [ ] The selected AgentCore service and Runtime protocol fit the workload.
- [ ] Current AWS documentation was checked for mutable service facts.
- [ ] IAM, JWT/OAuth, credential-provider, and resource-policy decisions use least privilege.
- [ ] Secrets are only presence-checked and never emitted or committed.
- [ ] Container/runtime contract, architecture, and health endpoints were verified locally.
- [ ] CDK synth/diff and relevant tests passed before a production deployment.
- [ ] Observability, data retention, and rollback/incident ownership are documented.
- [ ] Any template or support-file update triggers a new security review.
