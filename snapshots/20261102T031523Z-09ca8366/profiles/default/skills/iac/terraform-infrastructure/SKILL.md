---
name: terraform-infrastructure
description: Use when planning, provisioning, refactoring, or reviewing Terraform-managed infrastructure across environments. Covers state strategy, module boundaries, environment layout, validation, CI/CD integration, and operational safety for real IaC workflows.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [terraform, iac, infrastructure, devops, modules, state]
    related_skills: [terraform-module-library, deployment-pipeline-design]
---

# Terraform Infrastructure

## Overview

Use this skill for end-to-end Terraform infrastructure work: standing up new infrastructure, refactoring existing stacks, improving state and environment layout, reviewing Terraform repositories, or designing a safer delivery workflow around `plan` and `apply`.

This skill is intentionally broader than a module-authoring skill. It focuses on the operating model around Terraform: repository structure, environment separation, remote state, variable strategy, validation, CI/CD, and safety checks. When the task narrows into reusable module design, pair with `terraform-module-library`. For AWS-specific module conventions, use the AWS guidance inside `terraform-module-library`. When the main challenge is release workflow and approvals, pair with `deployment-pipeline-design`.

## When to Use

Use this skill when:
- Provisioning cloud infrastructure with Terraform
- Designing or reviewing Terraform repository layout
- Setting up remote state, locking, and environment isolation
- Refactoring ad hoc `.tf` code into modules and stacks
- Planning multi-environment workflows such as dev/stage/prod
- Adding validation, drift controls, policy checks, or CI/CD around Terraform
- Reviewing Terraform changes for operational safety and maintainability

Do not use this skill when:
- The user needs AWS CDK, Pulumi, CloudFormation, or another IaC system instead of Terraform
- The task is a very narrow reusable-module problem better handled by `terraform-module-library`
- The task is purely one provider-specific module implementation and the provider-focused skill is a better fit
- The user already has a stable Terraform workflow and only needs a small code edit inside one resource block

## Core Working Principles

1. **State strategy first.** Do not design repository layout or CI/CD before deciding how state is partitioned and locked.
2. **Environment isolation must be explicit.** Separate environments by backend key, workspace policy, directory layout, or repository boundaries — not by hope.
3. **Prefer reusable composition over copy-paste.** Shared infrastructure patterns should become modules once the shape stabilizes.
4. **Validation is part of authoring.** `fmt`, `validate`, variable validation, policy checks, and reviewed `plan` output are part of the workflow, not optional cleanup.
5. **Terraform is an operational system, not just code.** Access control, secrets handling, apply permissions, and rollback expectations matter as much as HCL quality.

## Phase 1 — Assess the Current Shape

Before changing anything, identify:
- Which cloud(s) and provider versions are involved
- Whether the repo is greenfield or already manages live resources
- How state is stored today
- How environments are separated
- What the promotion path looks like from development to production
- Whether applies happen locally, in CI, or both
- What the blast radius is if something goes wrong

Questions to answer early:
- Is this a new stack, a refactor, or a repair?
- Are resources already live and imported, or still to be created?
- Which parts must be reusable modules versus stack-specific composition?
- Who is allowed to run `apply`?
- What must happen before production apply is considered safe?

If the repository already exists, inspect the actual layout and current backend configuration before proposing a redesign.

## Phase 2 — Choose State and Environment Strategy

### Remote state
For team workflows, use remote state with locking and encryption. The exact backend depends on platform, but the policy is the same:
- state must not live only on one engineer's machine
- concurrent mutation must be controlled with locking or equivalent guardrails
- state access must be restricted to the right identities
- backups and recovery expectations must be understood

Typical examples:
- AWS: S3 backend with bucket versioning, encryption, and native S3 lockfiles (`use_lockfile = true`). Do not introduce DynamoDB locking for new stacks: the S3 backend's DynamoDB locking option is deprecated. For an existing DynamoDB-locked estate, plan and review its migration to S3 lockfiles explicitly.
- Azure: Azure Blob Storage with lease locking
- GCP: GCS with versioning and appropriate IAM
- Terraform Cloud/Enterprise: remote runs and remote state where appropriate

If the estate is already standardized on **OpenTofu**, keep the same operational expectations around remote state, locking, plan review, and environment isolation. Treat Terraform ↔ OpenTofu migration as an infrastructure change with explicit compatibility checks, provider-version review, and rollback planning rather than as a casual package swap.

### Environment separation
Pick one primary approach and apply it consistently:
- **Directory-per-environment** for explicit isolation and clearer review boundaries
- **Stack-per-environment** when infrastructure differs materially between environments
- **Workspaces** only when the differences are small and the team understands workspace risks
- **Separate repositories** when blast radius, permissions, or lifecycle boundaries demand it

Good default for many teams:
- reusable modules in `modules/`
- environment-specific root stacks in `live/` or `envs/`
- separate backend keys per environment
- production applies gated separately from development applies

## Phase 3 — Design Repository and Module Boundaries

A common baseline layout:

```text
terraform/
├── modules/
│   ├── network/
│   ├── compute/
│   └── database/
├── envs/
│   ├── dev/
│   ├── stage/
│   └── prod/
└── shared/
    ├── providers.tf
    └── conventions.md
```

Guidelines:
- Keep root stacks thin; they should compose modules rather than embed all logic inline.
- Module interfaces should be deliberate: clear variables, clear outputs, stable names.
- Do not turn one-off code into a module too early. Repetition plus stability is the signal.
- Avoid deeply nested abstraction that hides what resources actually exist.
- Keep provider configuration and backend concerns obvious at the stack level.

When the main task becomes module authoring quality, deeper interface design, or multi-cloud module patterns, hand off or pair with `terraform-module-library`.

## Phase 4 — Implement a Safe Authoring Workflow

Every Terraform change should pass through a predictable local workflow.

### Validation-host discipline
Before installing or invoking Terraform, confirm the user-authorized validation host. If the user designates a separate development or CI host for Terraform validation, do not install Terraform or alter tooling on the orchestration host. Instead, preserve portable commands and CI checks for the designated host, report honestly which non-Terraform checks were completed locally, and never imply that `init`, `validate`, or `plan` ran elsewhere.

Minimum authoring loop:
1. Update HCL with the smallest coherent change.
2. Run `terraform fmt`.
3. Run `terraform validate`.
4. Run `terraform plan` against the intended environment.
5. Review the plan for destructive actions, churn, and unintended drift.
6. Only then consider apply.

Prefer:
- `for_each` when stable identity matters
- variable validation blocks for important inputs
- explicit outputs for values needed by other modules or stacks
- clear tagging/labeling conventions
- pinning provider and module versions intentionally

Avoid:
- committing `.tfstate` files
- mixing environment-specific values directly into reusable modules
- silent defaults that create production surprises
- using workspaces as a substitute for a real environment model when the environments truly differ

## Phase 5 — Handle Existing Infrastructure Carefully

If Terraform is being introduced to resources that already exist:
- identify what must be imported versus recreated
- understand naming constraints and immutable properties before modeling resources
- verify whether provider defaults differ from the live environment
- plan the migration sequence so Terraform does not unintentionally replace critical resources

If the task is a refactor of existing Terraform:
- separate no-op structural changes from behavior-changing changes where possible
- use `moved` blocks and other migration techniques when appropriate
- reduce noise before major design changes so plans remain reviewable

This is the point where many "simple cleanups" become production incidents. Treat stateful resources conservatively.

## Phase 6 — Multi-Environment and Promotion Workflow

A mature Terraform workflow should answer:
- how changes move from lower to higher environments
- whether plans are environment-specific and reviewable
- who can approve production applies
- how drift is detected and surfaced
- what happens if a plan becomes stale before apply

Recommended baseline:
- independent plans per environment
- at least one human review of production plan output
- approval gate before production apply
- environment credentials separated appropriately
- plan artifacts tied to the commit being reviewed

For mature teams, add policy and governance controls to the workflow instead of relying on code review alone:
- policy-as-code or equivalent guardrails for high-risk resources and network exposure
- security scanning for Terraform changes in CI before apply is considered
- explicit cost and drift review for changes that can materially affect spend or compliance
- audit-friendly approval records for production changes and exception handling

If CI/CD design is the main task, use this skill for Terraform-specific constraints and pair with `deployment-pipeline-design` for broader release-architecture decisions.

## Phase 7 — Security and Secret Handling

Terraform should reference secrets carefully, not turn state into a secret dump.

Principles:
- Do not hardcode secrets in `.tf` files or commit secret-bearing tfvars files.
- Minimize secret values flowing through Terraform when the downstream platform can reference them directly.
- Assume Terraform state may contain sensitive values; secure backend access accordingly.
- Restrict who can read state, not just who can apply.
- Review outputs to avoid leaking secrets in plain text.

Also check:
- IAM or role assumptions used by CI and local developers
- provider credentials and rotation expectations
- policy guardrails for dangerous resource classes
- whether data sources or outputs are exposing more than intended

## Operational Checks

Before calling the workflow healthy, verify:
- state backend exists and is reachable
- locking works as expected
- environment separation is real, not nominal
- `fmt`, `validate`, and `plan` are part of normal practice
- plan review catches unexpected resource replacement or drift
- module and root-stack boundaries are understandable to another engineer
- production apply permissions are narrower than development experimentation
- state backup and recovery expectations are documented and have been exercised at least once
- failed applies, stale locks, and rollback/escalation paths are understood before an incident forces them
- enterprise access control, compliance boundaries, and audit expectations are reflected in the workflow design

## Common Pitfalls

1. **Designing modules before understanding state layout.**
   Great module boundaries do not save a broken backend or environment model.

2. **Using workspaces for everything.**
   Workspaces are useful, but they are not a universal multi-environment strategy.

3. **Letting root stacks become giant monoliths.**
   If everything lives in one root module, review and blast-radius control degrade quickly.

4. **Treating `plan` as optional.**
   Unreviewed applies are where Terraform stops being infrastructure as code and becomes infrastructure roulette.

5. **Ignoring import and migration risk.**
   Existing resources often have quirks that naive Terraform modeling will try to replace.

6. **Leaking secrets through state or outputs.**
   Backend security matters because state often contains more than teams expect.

7. **Over-abstracting too early.**
   A bad shared module can spread mistakes faster than copy-paste code.

8. **`terraform fmt -check` before `terraform fmt -recursive`.**
   Running `-check` first surfaces drift without fixing it; you still need the auto-fix pass. Go straight to `fmt -recursive`, confirm clean with `-check`.

9. **Grep-based verification hitting provider binaries.**
   `grep -r "dynamodb" stacks/` will match text inside `.terraform/providers/*/terraform-provider-aws_*` binaries — false positive. Scope absence-checks to source files only: `grep -rq --include="*.tf" --include="*.example" "pattern" stacks/`.

10. **Bootstrap stack must use `backend "local" {}`.**
    A bootstrap stack that creates the remote state bucket must use a local backend — it cannot reference the bucket it is about to create. Document this explicitly and `prevent_destroy = true` the bucket resource.

## CI and Formatting Preflight

Treat formatting as a release gate, not cosmetic cleanup. Before publishing a Terraform checkpoint:

1. **Always run `terraform fmt -recursive` (auto-fix) before `terraform fmt -check`.** Running `-check` first produces a non-zero exit that shows what would change but changes nothing; you then need a second pass to fix it. Go straight to `fmt -recursive`, then verify clean with `-check`. This is the correct sequence.
2. Run `terraform fmt -check -recursive` for every Terraform root stack in scope.
3. If the user designates another development host or CI as the authorized Terraform validation environment, do not install or run Terraform on the orchestration host. Report that limitation precisely and keep portable verification commands in the repository.
4. When CI is the first available formatter, wait for its result before declaring the checkpoint clean. If it reports formatting drift, include **all** reported formatting-only files together in one corrective change; do not leave sibling formatter changes unstaged after opening a PR.
5. For stacks with a remote backend unavailable to CI, run `terraform init -backend=false` before `terraform validate`.

## Verification Checklist

- [ ] The state backend and locking strategy are defined
- [ ] Environment separation is explicit and reviewable
- [ ] Module boundaries are justified rather than accidental
- [ ] Root stacks are understandable and not overly monolithic
- [ ] `terraform fmt`, `terraform validate`, and `terraform plan` are part of the workflow
- [ ] The authorized Terraform validation host is confirmed; checks not run locally are explicitly identified
- [ ] CI formatting has been checked before declaring a published checkpoint clean, and all formatter-reported files are included together
- [ ] Sensitive data handling is compatible with the chosen backend and state access model
- [ ] Production apply permissions and approval flow are clear
- [ ] The proposed layout can be maintained by someone other than the original author
- [ ] Any deeper module-design work is routed to `terraform-module-library`, including its AWS-specific module guidance when relevant

## Reference Files

| File | Contents |
|------|----------|
| [references/aws-s3-lockfile-lambda-patterns.md](references/aws-s3-lockfile-lambda-patterns.md) | S3 native lockfile backend config, bootstrap stack pattern, Lambda `logging_config`, API GW HTTP API access logs, Lambda permission scoped to `execution_arn`, least-privilege IAM inline policy, Terraform binary install without admin (macOS), verification script pitfalls (`((PASS++))` and binary grep) |
