---
name: aws-debugging-lambda-timeouts
description: "Use when the task involves debugging lambda timeouts in AWS. Debugs AWS Lambda function timeout failures by systematically analyzing function configuration, CloudWatch logs and metrics, VPC/networking, cold starts, memory constraints, and downstream dependencies to identify root causes with actionable fixes. Use when a Lambda function is timing out or approaching its timeout limit."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, lambda, troubleshooting, timeouts]
    related_skills: [cloud-architect, aws-serverless, aws-observability]
---

# Debugging Lambda Timeouts

## Overview

This skill covers debugging lambda timeouts workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/serverless-skills/debugging-lambda-timeouts` into Hermes-native skill format for the local `iac` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-debugging-lambda-timeouts`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Debug a Lambda timeout

To investigate and resolve Lambda timeout issues, follow the procedure exactly.
See [Lambda timeout debugging procedure](references/lambda-timeout-debugging.md).

The procedure collects function configuration, CloudWatch metrics and logs, dependency
analysis, and cold start patterns. If Lambda code is provided, it also reviews the code
for timeout-prone patterns. Results are compiled into a structured debugging report with
prioritized recommendations.

## Troubleshooting

### Function not found

Verify the function name and region. Use `aws lambda list-functions --region <region>`
to list available functions.

### No logs available

The function may not have been invoked recently or logging may be disabled. Check the
function's log group configuration and invocation metrics.

### Access denied errors

Verify AWS credentials have permissions for Lambda, CloudWatch Logs, and CloudWatch
Metrics. See the full procedure for details.

### Log query time range issues

If CloudWatch Logs Insights queries fail with time range errors, reduce the analysis
window or check log group retention settings. See the full procedure for details.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
