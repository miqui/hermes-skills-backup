---
name: aws-connecting-lambda-to-api-gateway
description: "Use when the task involves connecting lambda to api gateway in AWS. Connects an existing AWS Lambda function to Amazon API Gateway by creating a REST or HTTP API with resource/method setup, Lambda proxy integration, permissions, and deployment. Always use this skill when connecting Lambda to API Gateway — it handles CORS, throttling, access logging, and production security hardening that are easy to miss."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, lambda, api-gateway, integration]
    related_skills: [cloud-architect, aws-serverless, aws-creating-api-gateway-stage]
---

# Connecting Lambda to API Gateway

## Overview

This skill covers connecting lambda to api gateway workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/serverless-skills/connecting-lambda-to-api-gateway` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-connecting-lambda-to-api-gateway`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Connect a Lambda function to API Gateway

To create a REST API and wire it to a Lambda function, follow the procedure exactly.
See [Lambda to API Gateway connection procedure](references/lambda-gateway-api.md).

The procedure supports configurable authorization types (NONE, AWS_IAM,
COGNITO_USER_POOLS, CUSTOM), optional API key requirements, CORS setup, and
production security hardening including throttling and access logging.

## Troubleshooting

### 502 Bad Gateway

The Lambda function must return a proxy-compatible response with `statusCode`,
`headers`, and a stringified `body`. See the full procedure for format details.

### Permission denied invoking Lambda

Ensure `lambda:InvokeFunction` permission was added with the correct API Gateway
source ARN. See the full procedure for details.

### CORS errors in browser

Verify `enable_cors` was set to true, the OPTIONS method was created, and CORS
headers are configured in both method and integration responses.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
