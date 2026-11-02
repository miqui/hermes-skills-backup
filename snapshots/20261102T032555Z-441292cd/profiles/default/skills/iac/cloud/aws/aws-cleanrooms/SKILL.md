---
name: aws-cleanrooms
description: "Use when the task involves aws clean rooms in AWS. Troubleshoots and debugs AWS Clean Rooms collaboration issues related to IAM roles, S3 bucket policies, KMS keys, Lake Formation permissions, and CloudWatch logging for custom ML model training and inference jobs. Use when a customer reports permission failures, access errors, or log publishing issues in Clean Rooms."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, analytics, privacy, collaboration]
    related_skills: [cloud-architect, aws-querying-data-lake, aws-exploring-data-catalog]
---

# AWS Clean Rooms

## Overview

This skill covers aws clean rooms workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/analytics-skills/aws-cleanrooms` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-cleanrooms`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Common tasks

### Debugging Clean Rooms errors

Determine the failure type:

**Access denied or permission error?** → See [permission debugging procedure](references/permission-debugging.md). Covers IAM role policies (inline + attached managed), S3 bucket policies, KMS key policies, Lake Formation permissions, and cross-account trust.

**Missing CloudWatch logs for custom model jobs?** → See [custom model logging debugging procedure](references/custom-model-logging-debugging.md). Covers Configured Model Algorithm Association privacy configuration, ML Configuration role permissions, and log group verification.

## Additional resources

- [Clean Rooms Service Role Setup](https://docs.aws.amazon.com/clean-rooms/latest/userguide/setting-up-roles.html)
- [Cross-service Confused Deputy Prevention](https://docs.aws.amazon.com/clean-rooms/latest/userguide/cross-service-confused-deputy-prevention.html)
- [ML Roles Documentation](https://docs.aws.amazon.com/clean-rooms/latest/userguide/ml-roles.html)
- [Lake Formation Onboarding](https://docs.aws.amazon.com/lake-formation/latest/dg/onboarding-lf-permissions.html)

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
