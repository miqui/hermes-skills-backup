---
name: aws-setting-up-cloudtrail-multi-region
description: "Use when the task involves setting up cloudtrail multi-region in AWS. Enables a multi-region AWS CloudTrail trail with S3 log storage, CloudWatch Logs integration, and CloudWatch Logs Insights queries for security monitoring and compliance auditing. Use when setting up centralized API activity logging across all AWS regions."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, cloudtrail, audit, security]
    related_skills: [cloud-architect, aws-observability, aws-securing-s3-buckets]
---

# Setting Up CloudTrail Multi-Region

## Overview

This skill covers setting up cloudtrail multi-region workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/operations-skills/setting-up-cloudtrail-multi-region` into Hermes-native skill format for the local `iac` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-setting-up-cloudtrail-multi-region`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Set up a multi-region trail

To create a centralized multi-region CloudTrail trail with S3 storage, CloudWatch
Logs integration, and log analysis, follow the procedure exactly.
See [CloudTrail multi-region setup procedure](references/cloudtrail-multi-region-setup.md).

## Troubleshooting

### S3 bucket already exists

Choose a different globally unique name, or add a timestamp or organization identifier.

### Permission denied errors

Verify your identity with `aws sts get-caller-identity`. Ensure your user/role has required actions attached. Do NOT use `*FullAccess` managed policies.

### Trail not logging

Verify IAM role permissions, check S3 bucket policy allows CloudTrail access, and ensure the trail is started with `start-logging`.

### Missing events in CloudWatch

Allow 5-15 minutes for initial log delivery. Verify the CloudWatch Logs role ARN is correct and the log group exists in the same region as the trail.

### Opt-in region events not appearing

This is normal — events from opt-in regions may take several hours. Wait up to 24 hours before investigating further.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
