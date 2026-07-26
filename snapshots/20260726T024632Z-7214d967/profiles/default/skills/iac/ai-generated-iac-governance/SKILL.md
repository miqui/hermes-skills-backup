---
name: ai-generated-iac-governance
description: Use when AI agents generate, modify, review, or propose infrastructure-as-code changes and the work needs governance, policy-as-code guardrails, blast-radius review, validation evidence, approval gates, and production-safety controls before deployment.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [iac, governance, ai-agents, policy-as-code, opa, terraform, cloudformation, cdk, security, review]
    related_skills:
      - secure-agent-skills
      - skill-security-review-gates
      - terraform-infrastructure
      - aws-cloudformation
      - aws-cdk
      - deployment-pipeline-design
      - requesting-code-review
      - cloud-architect
---

# AI-Generated IaC Governance

## Overview

Use this skill when an AI agent generates, modifies, reviews, remediates, or proposes infrastructure-as-code. AI-generated IaC is high leverage: a small diff can create public exposure, over-broad identity permissions, destructive replacement, secret leakage, or major cost impact. Syntax-valid IaC is not automatically safe IaC.

This skill defines a governance and evidence workflow for catching what agents get wrong before production does. It does not replace tool-specific IaC skills. Pair it with `terraform-infrastructure`, `aws-cloudformation`, `aws-cdk`, `crossplane`, `ansible`, `kubernetes`, or other platform skills for implementation details. Pair it with `secure-agent-skills` and `skill-security-review-gates` when the governance question also involves approving the agent skill, prompt package, or automation that produced the IaC.

Core rule: agents may propose and validate infrastructure changes, but production-impacting IaC requires explicit blast-radius classification, policy-as-code evaluation, reviewable plan/diff evidence, and human approval before apply/deploy.

## When to Use

Use this skill when:
- An AI agent writes or edits Terraform/OpenTofu, CDK, CloudFormation, Pulumi, Crossplane, Kubernetes manifests, Helm charts, Kustomize overlays, Ansible, Bicep, ARM templates, or similar IaC
- Reviewing a pull request, plan, diff, module, construct, composition, playbook, or pipeline that was produced or materially changed by an agent
- Designing guardrails for agent-authored infrastructure changes before merge, apply, deploy, or promotion
- A team asks how to catch mistakes in AI-generated infrastructure code before production
- Choosing which validation, policy-as-code, cost, security, and approval gates should apply to agent-generated IaC
- Deciding what evidence must be attached to an IaC change for auditability and reviewer confidence
- Creating CI/CD gates for AI-authored infrastructure changes
- Evaluating whether an agent should be allowed to run plan, synth, diff, dry-run, apply, deploy, or remediation commands

Do not use this skill as the only guide when:
- The user needs general Terraform architecture, state layout, modules, or environment strategy; load `terraform-infrastructure`
- The user needs AWS CDK implementation details; load `aws-cdk`
- The user needs CloudFormation implementation/troubleshooting; load `aws-cloudformation`
- The user needs Kubernetes operations or manifest troubleshooting; load `kubernetes`
- The user needs to review the safety of Hermes skills themselves; load `secure-agent-skills` and `skill-security-review-gates`
- The task is a general application-code review unrelated to infrastructure; load `requesting-code-review`

## Core Governance Principles

1. **Classify blast radius before execution.** The stricter gates are driven by the environment and resource class, not by how confident the agent sounds.
2. **Prefer read-only evidence before mutation.** Agents should gather diffs, plans, validation output, and policy results before any apply/deploy action.
3. **Policy-as-code is a default guardrail.** Use OPA/Open Policy Agent or equivalent policy tooling where organization standards can be expressed as rules.
4. **Production approval is separate from generation.** An agent that produced a change must not be the only reviewer or approver for production-impacting IaC.
5. **Plans and diffs must be reviewable.** Reduce noisy churn so reviewers can see destructive, replacement, identity, network, data, and cost changes clearly.
6. **Credential scope matters.** Agent workflows should not rely on ambient production credentials unless explicitly approved and constrained.
7. **Exceptions must be explicit.** A failed policy or risky plan can be overridden only with scoped rationale, owner, approver, and expiry/re-review trigger.
8. **Tool output beats generated claims.** Do not trust comments, summaries, or explanations in generated IaC unless backed by real validation, plan, diff, or policy output.

## Blast-Radius Classification

Classify every AI-generated IaC change before choosing gates.

| Level | Scope | Examples | Minimum governance |
| --- | --- | --- | --- |
| 0 | Documentation or local examples only | README snippets, sample modules not wired to accounts | Syntax/lint check when feasible; no apply credentials |
| 1 | Sandbox or throwaway dev | Isolated test account/project/namespace with no sensitive data | Tool validation, policy scan, plan/dry-run review |
| 2 | Shared non-production | Shared dev/stage infrastructure, persistent preview envs | Independent review, policy-as-code, cost review if material, plan artifact |
| 3 | Production-adjacent | Shared networking, identity, state backends, CI deploy roles, persistent data in non-prod | Elevated review, explicit replacement/destruction check, exception record for failed policies |
| 4 | Production or security/compliance boundary | IAM, network perimeter, databases, encryption, logging, backups, state, audit, production workloads | Human production approval, policy-as-code pass or recorded exception, reviewed plan/diff, rollback/migration path, audit evidence |

When uncertain, classify upward. Identity, network, state, secrets, data stores, encryption, backups, audit logging, and production deployment permissions are high-risk even when the diff is small.

## AI-Generated IaC Risk Classes

Review agent-generated IaC for these failure modes:

### Identity and access
- Over-broad IAM policies such as `*` actions or resources without justification
- Trust policies that allow unintended principals, services, accounts, or federated identities
- CI/CD roles that can mutate production without review
- Generated admin roles, wildcard permissions, or privilege-escalation paths

### Network and public exposure
- Public security group ingress, open load balancers, public databases, public buckets, broad firewall rules
- Missing private endpoint, VPC, subnet, route table, DNS, or security-group constraints
- NAT/data-transfer patterns that unexpectedly increase cost or exposure

### Data protection and secrets
- Secrets hardcoded in IaC, tfvars, templates, manifests, user data, or outputs
- Terraform/OpenTofu state containing sensitive values without appropriate backend controls
- Missing encryption, KMS key policy, rotation, backup, retention, or deletion protection
- Outputs or logs that reveal credentials, tokens, connection strings, or private endpoints

### Destruction and replacement
- Resource replacement caused by immutable field changes
- Removed resources hidden inside large generated refactors
- Missing `moved` blocks, import plans, or migration sequencing for existing infrastructure
- Force-delete, skip-final-snapshot, auto-destroy, or low-retention settings copied into persistent environments

### Policy, compliance, and audit
- Missing tags/labels, ownership, cost-center, data-classification, or audit controls
- Disabled logging, monitoring, tracing, CloudTrail/audit logs, object access logs, or flow logs
- Policy exceptions suggested casually or without owner/expiry
- Generated code that passes syntax checks but violates organization rules

### Supply chain and drift
- Unpinned providers, modules, containers, GitHub Actions, Helm charts, or remote modules
- Floating `latest`, default branches, unreviewed module sources, or unverified registries
- Generated code using deprecated resources, hallucinated arguments, or provider-version mismatches
- Drift/import assumptions that cause IaC tools to recreate or take ownership of the wrong resources

### Cost and capacity
- Oversized instances, excessive replicas, expensive managed services, high-retention logs, cross-region replication, unnecessary NAT gateways, or high data-transfer patterns
- Missing budgets, cost alerts, autoscaling bounds, or lifecycle policies
- Agent-optimized convenience that increases recurring spend without review

## Validation Stack

Choose validation based on the IaC system and blast radius. Run commands from the target repository with scoped credentials and environment selection. Do not run apply/deploy merely to prove the generated code works.

### Terraform / OpenTofu
Minimum checks:
```bash
terraform fmt -check -recursive
terraform validate
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
```

Common guardrails:
```bash
tflint --recursive
checkov -d .
trivy config .
infracost breakdown --path .
conftest test tfplan.json
```

Review the plan for adds, changes, destroys, replacements, IAM/network changes, data stores, state backends, and output changes. For mature workflows, evaluate policy against the JSON plan, not only static HCL.

### CloudFormation
Minimum checks:
```bash
cfn-lint template.yaml
aws cloudformation validate-template --template-body file://template.yaml
```

Common guardrails:
```bash
cfn-guard validate --rules rules.guard --data template.yaml
```

For production-impacting changes, use change sets and review replacement/destruction before execution.

### AWS CDK
Minimum checks:
```bash
cdk synth
cdk diff
```

Common guardrails:
- cdk-nag / AwsSolutionsChecks where applicable
- CloudFormation validation and policy checks on synthesized templates
- review generated IAM policies and CloudFormation replacement semantics

### Kubernetes, Helm, Kustomize, and Crossplane
Minimum checks:
```bash
kubectl apply --dry-run=server -f <manifest-or-dir>
helm template <release> <chart> --values <values.yaml>
kustomize build <overlay>
```

Common guardrails:
- OPA Gatekeeper constraints for admission policy
- Kyverno policies where the cluster standardizes on Kyverno
- schema validation against installed CRDs
- Conftest/OPA checks against rendered manifests
- namespace, RBAC, NetworkPolicy, Pod Security, resource limits, and secret handling review

### Ansible
Minimum checks:
```bash
ansible-playbook --syntax-check playbook.yml
ansible-lint playbook.yml
ansible-playbook --check --diff playbook.yml
```

Review `become`, privilege escalation, inventory targeting, idempotency, secret handling, and whether generated tasks mutate more hosts than intended.

## OPA / Policy-as-Code Gate

OPA/Open Policy Agent should be explicit in AI-generated IaC governance, not implied. Use OPA where organization standards can be expressed as rules and evaluated before merge, apply, deploy, or admission.

Recommended patterns:
- **Conftest for repository and plan checks**: evaluate Terraform plan JSON, Kubernetes manifests, Helm-rendered YAML, CloudFormation templates, Dockerfiles, and other structured files before merge.
- **OPA Gatekeeper for Kubernetes admission**: enforce cluster policies such as required labels, allowed registries, resource limits, restricted hostPath usage, and prohibited privileged pods.
- **Pipeline-integrated OPA evaluation**: run policy checks as required CI jobs for AI-generated IaC pull requests.
- **Policy bundle ownership**: treat policies as reviewed artifacts with owners, versioning, tests, and exception processes.
- **Exception workflow**: require explicit, scoped, time-bounded approval for failed policies rather than silently disabling rules.

OPA is not the only valid policy engine. Use cloud-native policy systems, Sentinel, cfn-guard, Azure Policy, GCP Organization Policy, AWS Config/CloudFormation Guard, Kyverno, or admission controllers where they fit the platform. The governance requirement is that policy decisions are automated, evidence-producing, and reviewed when bypassed.

OPA evidence should include:
- policy bundle or ruleset name/version
- target input, such as HCL, plan JSON, rendered manifests, or templates
- pass/fail output
- skipped policies and why they were skipped
- exception ID or approval record for failures accepted anyway

## Required Evidence Packet

Before approving AI-generated IaC beyond Level 0, collect a compact evidence packet:

```markdown
AI-Generated IaC Review

AI involvement:
- Agent/tool/model:
- Prompt or change request summary:
- Files generated or modified:

Blast radius:
- Level: 0 | 1 | 2 | 3 | 4
- Target environment/account/project/cluster:
- Sensitive resource classes touched: identity | network | data | state | secrets | production | other

Validation:
- Syntax/format validation:
- Plan/diff/change-set/dry-run artifact:
- Policy-as-code results, including OPA/conftest/gatekeeper where applicable:
- Security scan results:
- Cost review/infracost result if material:

Plan review:
- Adds:
- Changes:
- Destroys:
- Replacements:
- IAM/network/data/security-impacting changes:

Decision:
- Reviewer:
- Approver:
- Decision: approved | approved with constraints | rejected | needs changes
- Exceptions:
- Residual risks:
- Rollback/migration/import notes:
```

For Level 3 and Level 4 changes, preserve the evidence packet in the pull request, change ticket, deployment record, or other audit-friendly system.

## Human Approval Gates

Use stricter gates as blast radius increases.

### Level 0 to Level 1
- Agent may generate code and run local/static validation.
- Do not provide broad cloud credentials just for examples.
- Review before any shared environment apply.

### Level 2
- Require an independent reviewer who did not generate the IaC.
- Require plan/diff or dry-run output.
- Require policy-as-code checks where policies exist.
- Require cost review for persistent or scalable resources.

### Level 3
- Require elevated review for identity, network, state, data, and CI/CD permission changes.
- Require explicit replacement/destruction review.
- Require policy failures to be fixed or documented as scoped exceptions.
- Prefer CI-executed plans over local plans with ambient credentials.

### Level 4
- Agent must not self-approve or directly apply production infrastructure.
- Require human-reviewed production plan, change set, diff, dry-run, or rendered manifests.
- Require OPA or equivalent policy-as-code pass, or a recorded exception approved by the correct owner.
- Require rollback, migration, import, or restore notes for stateful/destructive changes.
- Require approval record tied to the exact commit/artifact being applied.

## Review Workflow

1. **Identify AI involvement.** Determine what the agent generated, edited, summarized, or approved.
2. **Inspect the repository shape.** Find IaC system, environment layout, state/backend config, CI workflow, and policy directories.
3. **Classify blast radius.** Use the highest applicable level.
4. **Run read-only validation.** Format, validate, synth, template, lint, dry-run, plan, or change-set creation as appropriate.
5. **Run policy and security scans.** Include OPA/conftest/gatekeeper where applicable. Add tool-specific scanners.
6. **Review semantic risk.** Focus on identity, network, data protection, state, secrets, destruction/replacement, cost, and auditability.
7. **Reduce noise.** Ask the agent or implementer to split cosmetic/refactor churn from behavior-changing IaC before production review.
8. **Collect evidence.** Attach plan/diff/policy/cost outputs and summarize risky deltas.
9. **Decide.** Approve, approve with constraints, reject, or require changes. Record exceptions explicitly.
10. **Verify post-merge controls.** Ensure CI, policy gates, protected environments, and approval rules enforce the intended workflow.

## Common Pitfalls

1. **Treating `validate` as enough.** Syntax validation does not catch public exposure, excessive IAM, destructive replacement, missing encryption, or cost risk.
2. **Letting the generating agent self-review.** Use fresh review context for production-impacting IaC.
3. **Skipping OPA because policies are “future work.”** If the organization has repeatable infrastructure standards, encode them as policy-as-code and make policy results part of the evidence packet.
4. **Accepting broad IAM for convenience.** Agents often over-generalize permissions; narrow actions, resources, conditions, and trust policies before approval.
5. **Hiding dangerous changes in large generated refactors.** Split formatting/module cleanup from behavior changes so plan review is readable.
6. **Applying from local ambient credentials.** Prefer scoped CI roles and protected environments, especially for Level 3/4 changes.
7. **Ignoring state and import reality.** Generated IaC can model a live resource incorrectly and trigger replacement or takeover mistakes.
8. **Forgetting cost gates.** Persistent resources, cross-region data, NAT, logging retention, managed databases, and autoscaling limits need cost review.
9. **Treating comments as proof.** Generated comments that claim encryption, backups, or least privilege must be verified against actual configuration and tool output.
10. **Disabling policies instead of recording exceptions.** A bypass without owner, scope, rationale, and re-review trigger is governance failure.

## Verification Checklist

- [ ] AI-generated or AI-modified files were identified
- [ ] Blast radius was classified and documented
- [ ] Tool-specific syntax/format/schema validation ran
- [ ] Plan, diff, change set, rendered manifest, or dry-run output was reviewed
- [ ] OPA/Open Policy Agent, Conftest, Gatekeeper, or equivalent policy-as-code checks ran where applicable
- [ ] Policy failures were fixed or recorded as explicit scoped exceptions
- [ ] IAM, network exposure, state, secrets, data protection, logging, backups, and deletion protection were reviewed when touched
- [ ] Destructive actions and replacements were separately summarized
- [ ] Cost impact was reviewed for persistent or scalable resources
- [ ] Provider/module/action/chart versions and remote sources were reviewed for pinning and supply-chain risk
- [ ] Production-impacting changes have human approval separate from the generating agent
- [ ] Evidence is tied to the exact commit/artifact/environment being approved
- [ ] Rollback, migration, import, or restore notes exist for stateful or destructive changes

## One-Shot Recipes

### Recipe: Review an AI-generated Terraform pull request
1. Load `terraform-infrastructure` for Terraform-specific workflow.
2. Identify changed `.tf`, `.tfvars`, lock, module, backend, and CI files.
3. Run `terraform fmt -check -recursive`, `terraform validate`, and `terraform plan -out=tfplan` for the target environment.
4. Convert the plan with `terraform show -json tfplan > tfplan.json`.
5. Run `tflint`, `checkov`, `trivy config`, and `conftest test tfplan.json` where available.
6. Summarize adds/changes/destroys/replacements plus IAM/network/data/state/cost changes.
7. Require human approval before apply for Level 3/4 changes.

### Recipe: Add OPA to an AI-IaC CI gate
1. Identify policy targets: Terraform plan JSON, rendered Kubernetes manifests, CloudFormation templates, or repo config.
2. Store policies in a reviewed directory such as `policy/` or `opa/` with tests and ownership.
3. Add a CI job that renders/generates the target input and runs `conftest test <input>` or the platform's OPA integration.
4. Make the CI job required for protected branches or protected environments.
5. Define an exception path requiring owner, approver, rationale, scope, and expiry.
6. Record policy results in the PR or deployment evidence packet.

### Recipe: Decide whether an agent may apply IaC
1. Determine blast radius and credential scope.
2. For Level 0/1, allow only sandbox-scoped credentials and reversible changes.
3. For Level 2, require plan and independent review before shared apply.
4. For Level 3/4, do not allow direct agent apply unless an explicit protected workflow already enforces human approval, scoped credentials, policy gates, and audit logging.
5. If controls are missing, restrict the agent to proposal, validation, and evidence collection only.
