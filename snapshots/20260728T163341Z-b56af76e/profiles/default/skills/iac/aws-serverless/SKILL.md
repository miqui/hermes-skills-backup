---
name: aws-serverless
description: "Use when the task involves aws serverless in AWS. Builds, deploys, manages, debugs, configures, and optimizes serverless applications on AWS using Lambda, API Gateway, Step Functions, EventBridge, and SAM/CDK. Covers cold starts, CORS debugging, event source mappings, troubleshooting, concurrency, SnapStart, Powertools, function URLs, EventBridge Scheduler, Lambda layers, Durable Functions, durable execution, checkpoint-and-replay, and production readiness. Use when the user mentions Lambda, API Gateway, Step Functions, SAM templates, CDK serverless stacks, DynamoDB stream triggers, SQS event sources, cold starts, timeouts, 502/504 errors, throttling, concurrency, CORS, Powertools, Durable Functions, durable execution, checkpoint-and-replay, or any event-driven architecture on AWS, even if they don't say 'serverless.' Do NOT use for EC2, ECS/Fargate containers, or Amplify hosting."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, lambda, api-gateway, event-driven, serverless]
    related_skills: [cloud-architect, aws-connecting-lambda-to-api-gateway, aws-debugging-lambda-timeouts]
---

# AWS Serverless

## Overview

This skill covers aws serverless workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/core-skills/aws-serverless` into Hermes-native skill format for the local `iac` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-serverless`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Routing

| User need | Action |
|-----------|--------|
| Building a new serverless app | Read [architecture.md](references/architecture.md) for pattern selection, then [deployment.md](references/deployment.md) for SAM/CDK templates |
| Debugging an error | Read [troubleshooting.md](references/troubleshooting.md) — starts with the 5 most common fixes |
| Optimizing performance or cost | Read [lambda.md](references/lambda.md) for cold starts and memory tuning, [production.md](references/production.md) for readiness checklist |
| Configuring event sources (SQS, DDB Streams, SNS) | Read [event-sources.md](references/event-sources.md) |
| Step Functions, EventBridge, or orchestration | Read [orchestration.md](references/orchestration.md) |
| Concurrency configuration | Read [concurrency.md](references/concurrency.md) |
| API Gateway setup | Read [api-gateway.md](references/api-gateway.md) |
| Common anti-patterns | Read the anti-patterns section in [production.md](references/production.md) |
| Starting with Powertools | Use [powertools-handler.py](assets/powertools-handler.py) as a template |
| Spans multiple areas | Read the most specific reference first, then consult others as needed |

## Files

| File | Content |
|------|---------|
| [lambda.md](references/lambda.md) | Runtime, memory/CPU, cold starts, SnapStart, layers, containers |
| [api-gateway.md](references/api-gateway.md) | REST vs HTTP API, stages, auth, throttling, mapping |
| [event-sources.md](references/event-sources.md) | SQS, DDB Streams, SNS, S3, Kinesis triggers |
| [orchestration.md](references/orchestration.md) | Step Functions, EventBridge rules/pipes/scheduler |
| [concurrency.md](references/concurrency.md) | Reserved vs provisioned, scaling, ESM concurrency |
| [architecture.md](references/architecture.md) | Patterns, reference architectures, service selection |
| [deployment.md](references/deployment.md) | SAM/CDK resource types, globals, fast iteration |
| [production.md](references/production.md) | Readiness checklist, observability, anti-patterns |
| [troubleshooting.md](references/troubleshooting.md) | Error → cause → fix for all serverless services |

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
