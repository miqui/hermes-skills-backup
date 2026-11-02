# Deployment and Operations

## Deployment approach

Use CDK for production AgentCore infrastructure so Runtime, Gateway, Identity, IAM, logging, network controls, artifact lifecycle, tags, and rollback behavior are reviewed in one change set. Starter CLI and shell examples are for local proof-of-concept work only.

Before provisioning, produce a plan covering:

- account, region, environment, data classification, and owners;
- Runtime protocol, artifact strategy, and required endpoint behavior;
- caller authentication and outbound credentials;
- IAM roles and exact resource/action scope;
- private-network/proxy requirements;
- logging, tracing, retention, alerting, and incident response;
- deployment approval and rollback strategy.

## Safe validation sequence

1. Run application tests, formatting/type/static checks, and dependency vulnerability checks.
2. Build the container for the target architecture and test health/request behavior locally.
3. Run CDK synth and inspect the resulting IAM policies, resource policies, secrets references, and log-retention controls.
4. Run CDK diff against the target environment and review replacements, destructive changes, public exposure, and permissions.
5. Obtain explicit approval before `cdk deploy` or any create/update/delete AWS command.
6. After deployment, run bounded smoke tests, examine traces/logs, and record the deployed version and rollback route.

The imported deployment shell script is preserved as a template but is intentionally not an automatic deployment mechanism.

## Runtime architecture patterns

### Direct HTTP Runtime

Use an application-defined request contract, health endpoint, structured request IDs, bounded streaming, input validation, and explicit error redaction. Keep CORS origin lists as narrow as possible and verify current AgentCore origin requirements.

### Gateway-backed tools

Gateway is appropriate when agents consume APIs, Lambda functions, or MCP services as tools. Create a clear schema, validate tool inputs at the target, apply least-privilege execution roles, and implement authorization independently of the agent prompt.

### AgentRegistry and evaluations

Catalog only resources with an accountable owner and a maintainable version/review process. Evaluation datasets and traces may contain sensitive content; apply collection minimization, retention, access controls, and review for every evaluator.

## Observability

Use consistent request/correlation IDs across Runtime, Gateway, tool target, and downstream calls. Capture latency, errors, tool invocations, and bounded business metrics. Do not record raw credentials or unnecessary prompt/user content. Follow `aws-observability` for CloudWatch, OTEL/ADOT, X-Ray, alarms, and log-query work.

## Framework selection

| Need | Reasonable starting point |
|---|---|
| Python agent with Bedrock/MCP integration | Strands plus FastAPI, after validating package versions |
| Tool server | FastMCP or a compatible MCP SDK with typed/validated tools |
| Rich web-agent event stream | AG-UI adapter only after confirming protocol/library versions |
| Agent collaboration | A2A server/card implementation with explicit capabilities and auth |
| Production AWS infrastructure | AWS CDK plus the relevant `aws-cdk`, `aws-iam`, and `aws-observability` skills |

## Deployment anti-patterns

- Relying on a prototype CLI deployment as the production control plane.
- Bypassing CDK review with automatic `--require-approval never` deployment.
- Broad roles, wildcard resource policies, or user access keys embedded in templates.
- Missing image/architecture validation, health checks, and telemetry.
- Treating a successful deploy command as proof that authentication, tool authorization, data isolation, or rollback works.
