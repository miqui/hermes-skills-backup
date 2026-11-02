---
name: aws-creating-api-gateway-stage
description: "Use when the task involves creating an api gateway stage in AWS. Creates an API Gateway stage with CloudWatch logging, X-Ray tracing, throttling, WAF integration, and IAM roles following AWS best practices. Use when deploying a REST API to different environments such as dev, test, or production."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, api-gateway, deployment, serverless]
    related_skills: [cloud-architect, aws-serverless, aws-connecting-lambda-to-api-gateway]
---

# Creating an API Gateway Stage

## Overview

This skill covers creating an api gateway stage workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/serverless-skills/creating-api-gateway-stage` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-creating-api-gateway-stage`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Create an API Gateway stage

To create a fully configured API Gateway stage with logging, throttling, WAF, and
authorization, follow the procedure exactly.
See [API Gateway stage creation procedure](references/create-api-gateway-stage.md).

## Troubleshooting

### CloudWatch logs not appearing

Verify the CloudWatch role permissions, log group existence, and that logging is
enabled at both stage and method levels. See the
[full procedure](references/create-api-gateway-stage.md) for details.

### Stage creation fails

Check REST API ID, deployment ID, IAM permissions, and stage naming conventions.

### WAF blocking legitimate requests

Review WAF logs, adjust rules or add exceptions, and consider count mode for testing.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
