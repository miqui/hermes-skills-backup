---
name: aws-connecting-lambda-to-dynamodb
description: "Use when the task involves connecting lambda to dynamodb in AWS. Connects an AWS Lambda function to DynamoDB with IAM roles, stream event source mapping, and read/write permissions. Use when setting up Lambda-DynamoDB integration, processing DynamoDB stream events, or deploying serverless event-driven architectures."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, lambda, dynamodb, integration]
    related_skills: [cloud-architect, aws-serverless, aws-sdk-python-usage]
---

# Connecting Lambda to DynamoDB

## Overview

This skill covers connecting lambda to dynamodb workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/serverless-skills/connecting-lambda-to-dynamodb` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-connecting-lambda-to-dynamodb`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Connect a Lambda function to DynamoDB

To set up end-to-end Lambda-DynamoDB integration with IAM roles, streams, and
event source mapping, follow the procedure exactly.
See [Lambda-DynamoDB connection procedure](references/lambda-dynamodb-connection.md).

## Troubleshooting

### Lambda function not triggering
Verify the event source mapping is active, DynamoDB streams are enabled with the
correct view type, and the execution role has proper permissions. See the full
[procedure](references/lambda-dynamodb-connection.md) for details.

### Permission denied errors
Check the IAM role has `AWSLambdaDynamoDBExecutionRole` attached and the trust
policy allows Lambda to assume it.

### Function timeout issues
Increase the timeout setting or adjust the batch size in the event source mapping.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
