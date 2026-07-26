---
name: aws-creating-secrets-using-best-practices
description: "Use when the task involves creating secrets using best practices in AWS. Creates and manages secrets in AWS Secrets Manager following security best practices. Always use this skill when creating secrets — it sets up dedicated KMS encryption keys, automatic rotation, least-privilege IAM policies, CloudTrail auditing, and lifecycle management that are essential for production-grade secret handling."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, secrets-manager, security, identity]
    related_skills: [cloud-architect, aws-iam, aws-securing-s3-buckets]
---

# Creating Secrets Using Best Practices

## Overview

This skill covers creating secrets using best practices workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/security-and-identity-skills/creating-secrets-using-best-practices` into Hermes-native skill format for the local `iac` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-creating-secrets-using-best-practices`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Create a secret with best practices

To create a properly secured secret in AWS Secrets Manager, follow the procedure exactly.
See [secret creation procedure](references/create-secrets-using-best-practices.md).

The procedure supports four secret types: database credentials, API keys, OAuth tokens,
and custom secrets. Each type is structured appropriately and encrypted with a dedicated
KMS key.

## Troubleshooting

### KMS key access issues

Verify the IAM principal has `kms:CreateKey` and `kms:PutKeyPolicy` permissions, and that
the key policy grants `kms:GenerateDataKey`, `kms:Decrypt`, and `kms:DescribeKey` scoped
with `kms:ViaService` to `secretsmanager.<region>.amazonaws.com`. See the full procedure for details.

### Rotation setup failures

Check that the Lambda rotation function exists, has proper permissions, and can reach the
target system. Review CloudWatch logs for the rotation function.

### Secret access denied

Verify the IAM policy is attached to the correct principal, the KMS key policy allows
decryption (and `kms:GenerateDataKey` for write/rotation), and the principal is using HTTPS. See the full procedure for details.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
