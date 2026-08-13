---
name: aws-troubleshooting-application-failures
description: "Use when the task involves application failure troubleshooting in AWS. Troubleshoots failing applications by discovering and analyzing CloudWatch log groups to identify error patterns, root causes, and actionable solutions. Use when an application is experiencing failures and log-based diagnosis is needed."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, troubleshooting, operations, incidents]
    related_skills: [cloud-architect, aws-observability, aws-serverless]
---

# Application Failure Troubleshooting

## Overview

This skill covers application failure troubleshooting workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/operations-skills/troubleshooting-application-failures` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-troubleshooting-application-failures`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Troubleshoot a failing application

To diagnose and resolve application failures using CloudWatch logs, follow the
procedure exactly. See [Application failure troubleshooting procedure](references/application-failure-troubleshooting.md).

## Troubleshooting

### No log groups found

Ask the user for specific log group names. Common patterns: `/aws/lambda/function-name`,
`/aws/apigateway/api-name`, or custom application log groups.

### Access denied errors

Verify AWS credentials have `logs:DescribeLogGroups`, `logs:DescribeLogStreams`,
`logs:StartQuery`, and `logs:GetQueryResults` permissions.

### Query timeouts

Reduce the time window or limit results. Large log groups may require multiple smaller queries.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
