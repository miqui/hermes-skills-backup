# Import Review and Source Map

## Decision record

- **Source:** User-supplied Bedrock AgentCore skill package and runtime templates.
- **Decision:** Approved with constraints for local Hermes use.
- **Constraints:** Documentation and templates are advisory. Check current official AWS documentation before using mutable facts; require explicit approval for provision, deploy, update, or delete actions; never copy credentials from examples into config/source/logs.
- **Owner:** Local Hermes profile owner.
- **Re-review trigger:** Any change to a template, package/version guidance, external URL, AWS protocol/API claim, or permission/authentication workflow.

## Normalization applied

1. Replaced foreign-agent metadata and tool names (`allowed-tools`, Claude/OpenClaw-specific paths and commands) with Hermes-native frontmatter and `native-mcp` guidance.
2. Removed floating-package installation instructions for privileged AWS access; any future MCP server must be reviewed and pinned.
3. Moved runnable source examples into clearly labelled `templates/`; they are not installation or deployment automation.
4. Replaced automatic/deploy-first guidance with a validation-first, explicit-approval workflow.
5. Added secret-redaction, least-privilege, policy, and data-governance constraints.
6. Separated broad Bedrock concerns to the installed `amazon-bedrock` skill to avoid routing duplication.

## Supplied source coverage

The normalized material incorporates operational guidance from the supplied AgentCore core, runtime core/deployment/protocol guides, gateway guides, credential/OAuth/policy guides, memory/browser/code-interpreter/observability/registry/evaluations guides, cross-service persistence notes, and six runtime/gateway templates.

The package also included example `gateway-deploy.sh` and `gateway-validate-deployment.sh` scripts. They are represented as review-only templates because the original deployment path can create or modify AWS infrastructure.

## Known limitations

- Source examples may reference package APIs, CLI flags, service endpoints, and protocol versions that drift.
- The custom-resource Lambda must be validated against the currently installed boto3/botocore service model and deployment framework before use.
- The templates do not grant production readiness by themselves; they need project-specific testing, IaC review, IAM validation, and rollout controls.
- Documentation MCP availability is separate from an authenticated AWS API MCP server.

## Review checklist

- [ ] AWS official docs/API references checked for the intended service and region.
- [ ] Framework/SDK versions matched to the project lockfile.
- [ ] All credentials, tokens, and URLs are supplied through secure project configuration—not copied from examples.
- [ ] The generated IaC diff, roles, resource policies, and log settings were reviewed.
- [ ] Deployment is explicitly approved and has a rollback path.
