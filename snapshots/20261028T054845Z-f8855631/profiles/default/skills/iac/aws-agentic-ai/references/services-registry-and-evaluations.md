# Services, Registry, and Evaluations

## Service routing

| AgentCore capability | Use for | Design focus |
|---|---|---|
| Runtime | Hosting agents or tools | Protocol, container, auth, scaling, health, session/state |
| Gateway | Turning APIs, Lambda, or MCP services into agent tools | Schema, target validation, authorization, credential providers |
| Memory | Managed short-/long-term agent memory | Tenant isolation, retention, retrieval correctness, cost |
| Identity | Inbound/outbound identity and credentials | OAuth/JWT/IAM choice, secret storage, rotation, scopes |
| Browser | Isolated browser automation | Session boundary, allowlists, data handling, interaction safety |
| Code Interpreter | Sandboxed code/data operations | Input/output controls, egress, artifact handling, cost limits |
| Observability | Traces, metrics, logs | Privacy, correlation, sampling, alarms, incident workflow |
| Agent Registry | Catalog/discovery of agents, tools, MCP servers, and skills | Ownership, metadata integrity, review lifecycle |
| Evaluations | Automated quality assessment | Dataset governance, evaluator validity, trace access, regression gates |

Verify current availability, regions, quotas, and API behavior before implementation.

## Agent Registry

Treat Registry records as organizational metadata, not executable trust assertions. Require an owner, version, lifecycle status, provenance, intended consumers, and security review before publishing. Search/discovery should expose only records appropriate to the caller. Registry MCP connectivity needs the same authentication/authorization review as every external MCP endpoint.

## Evaluations

Use evaluations after establishing good trace hygiene. Define the task, expected behaviors, failure taxonomy, dataset source, sensitive-data handling, judge/evaluator limitations, thresholds, review path, and regression policy. Avoid treating a single LLM-judge score as proof of safety or production readiness.

## Browser and Code Interpreter

Both capabilities execute actions beyond text generation. Bound their authority with strict inputs, limited allowed destinations/storage, tenant isolation, time/size/cost controls, auditing, and explicit user approval for consequential actions. Never use a sandbox boundary as the only control for credentials or production-impacting downstream systems.

## Memory and external persistence

Memory improves continuity but does not replace application data governance. Choose explicit namespaces, identity boundaries, retention/deletion flows, and recovery behavior. For artifacts, prefer a durable store with narrow IAM and lifecycle controls. Validate that deleted users/tenants cannot be retrieved through semantic recall or stale indexes.

## Source coverage

This reference consolidates the supplied AgentCore material for Gateway, Memory, Browser, Code Interpreter, Observability, Registry, Evaluations, sync/governance, and cross-service persistence. The source inventory records the files and the normalization rationale.
