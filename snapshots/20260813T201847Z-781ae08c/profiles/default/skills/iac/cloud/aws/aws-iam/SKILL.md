---
name: aws-iam
description: "Use when the task involves aws iam — common pitfalls in AWS. Verified corrections for IAM behaviors that AI agents frequently get"
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, identity, policies, sts, security]
    related_skills: [cloud-architect, aws-creating-secrets-using-best-practices, aws-setting-up-ec2-instance-profiles]
---

# AWS IAM — Common Pitfalls

## Overview

This skill covers aws iam — common pitfalls workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/core-skills/aws-iam` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-iam`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Verified Edge Cases

**CloudTrail:**

- AcceptHandshake/DeclineHandshake logged in ACTING account ONLY, not management account. Organization trail required for centralization.
- ConsoleLogin region varies by endpoint/cookies, NOT always us-east-1. `?region=` forces specific region.

**STS:**

- GetSessionToken restrictions: (1) No IAM APIs unless MFA included (2) No STS except AssumeRole and GetCallerIdentity.
- Cross-account AssumeRole to opt-in region: TARGET account must enable region, not calling account.
- Role chaining: max 1-hour session.

**Organizations:**

- Suspended/closed accounts CANNOT be removed until permanently closed (~90 days). Remove FIRST, then close.
- Policy management delegation: use PutResourcePolicy, NOT register-delegated-administrator.
- AI opt-out policies: management account required by default.
- Organizations policy types for ListPolicies filter: SERVICE_CONTROL_POLICY, TAG_POLICY, BACKUP_POLICY, AISERVICES_OPT_OUT_POLICY, CHATBOT_POLICY, DECLARATIVE_POLICY_EC2, RESOURCE_CONTROL_POLICY.

**SDK Specifics:**

- Organizations: `DuplicatePolicyAttachmentException` (not PolicyAlreadyAttachedException).
- Boto3 IAM AccessKey: methods are `activate()`, `deactivate()`, `delete()` — NO `update()`.
- Instance profiles: waiter + `time.sleep(10)` pattern.
- Managed policy max versions: 5.

**SAML:**

- Encrypted assertions URL: `https://region-code.signin.aws.amazon.com/saml/acs/IdP-ID`.
- Private key from IdP uploaded to IAM in .pem format.

**Policy Evaluation:**

- ForAllValues with empty/missing key: evaluates to true (vacuous truth). To avoid that, use a `Null` condition in addition to the `ForAllValues` on **the same context key** to require that key to be present and non-null. For example, when evaluating the `aws:TagKeys` context key:

```
{
    "Version": "2012-10-17",
    "Statement": {
        "Effect": "Allow",
        "Action": "ec2:RunInstances",
        "Resource": "*",
        "Condition": {
            "ForAllValues:StringEquals": {
                "aws:TagKeys": ["Alpha", "Beta"]
            },
            "Null": {
                "aws:TagKeys": "false"
            }
        }
    }
}
```

- Resource-based policies granting to IAM user ARN bypass permissions boundaries in same account.
- 8 privilege escalation actions via direct IAM policy manipulation: PutGroupPolicy, PutRolePolicy, PutUserPolicy, CreatePolicy, CreatePolicyVersion, AttachGroupPolicy, AttachRolePolicy, AttachUserPolicy.
- `iam:PassRole` with `Resource: "*"` + create/update on a compute service (EC2 `RunInstances`, Lambda `CreateFunction`/`UpdateFunctionConfiguration`, ECS `RegisterTaskDefinition`, Glue, SageMaker, CloudFormation, etc.) = privilege escalation to any passable role in the account, including Administrator. Scope `Resource` to specific role ARNs or an IAM path; optionally constrain with `iam:PassedToService` / `iam:AssociatedResourceArn`. See [IAM User Guide — Grant a user permissions to pass a role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_passrole.html).

**MFA:**

- Unassigned virtual MFA devices auto-deleted when adding new ones.
- MFA resync-only policy NotAction needs exactly: iam:ListMFADevices, iam:ListVirtualMFADevices, iam:ResyncMFADevice.

**SigV4:**

- IncompleteSignatureException includes SHA-256 hash of Authorization header for transit modification diagnosis.

**Service-Specific Roles:**

- Redshift Serverless trust policy: include BOTH `redshift-serverless.amazonaws.com` AND `redshift.amazonaws.com` as service principals (per AWS docs; omitting serverless causes `Not authorized to get credentials of role` on COPY).
- IAM OIDC providers: thumbprints no longer required for most providers (AWS verifies via trusted CAs since 2022).

**Policy Summary Display:**

- Single statement with multi-service wildcard actions (e.g. `codebuild:*`, `codecommit:*`) + service-specific resource ARNs: each resource appears ONLY under its matching service's summary (CodeBuild ARN under CodeBuild, etc.). A resource whose service prefix matches NO action in the statement is the only case where it appears in all action summaries ("mismatched resource").

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
