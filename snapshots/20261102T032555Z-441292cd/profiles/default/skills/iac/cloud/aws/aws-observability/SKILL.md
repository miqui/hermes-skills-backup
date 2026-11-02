---
name: aws-observability
description: "Use when the task involves aws observability in AWS. Builds, configures, debugs, and optimizes AWS observability using CloudWatch (Logs Insights, Metrics, Alarms, Dashboards, EMF), X-Ray, CloudTrail, and ADOT. Covers Log Insights query syntax (fields, filter, stats, parse, pattern, join, subqueries), alarm configuration (metric, composite, anomaly detection, missing data treatment), dashboard design, custom metrics (PutMetricData, EMF, metric filters), X-Ray tracing (ADOT, sampling rules, annotations vs metadata), ADOT collector config, and CloudTrail auditing. Use when the user mentions CloudWatch, Log Insights, alarms, INSUFFICIENT_DATA, dashboards, custom metrics, EMF, X-Ray, traces, sampling, CloudTrail, who deleted, ADOT, OpenTelemetry, observability, monitoring, synthetics, canaries, or troubleshooting alarm behavior. Do NOT use for application logging setup, container log drivers, or security threat detection."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, cloudwatch, cloudtrail, xray, monitoring]
    related_skills: [cloud-architect, aws-setting-up-cloudtrail-multi-region, aws-setting-up-cloudwatch-alarm-notifications]
---

# AWS Observability

## Overview

This skill covers aws observability workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/core-skills/aws-observability` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-observability`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Routing

| User need | Action |
|-----------|--------|
| Writing Log Insights queries | Read [log-insights.md](references/log-insights.md) |
| Configuring alarms (metric, composite, anomaly) | Read [alarms.md](references/alarms.md) |
| Publishing custom metrics or using EMF | Read [metrics.md](references/metrics.md) |
| Setting up X-Ray tracing or ADOT | Read [tracing.md](references/tracing.md) |
| Building dashboards | Read [dashboards.md](references/dashboards.md) |
| Debugging observability issues | Read [troubleshooting.md](references/troubleshooting.md) — starts with the 5 most common fixes |
| Debugging canary failures | Read [synthetics.md](references/synthetics.md) — see Common failures table |
| CloudTrail operational auditing | Read [cloudtrail.md](references/cloudtrail.md) |
| Setting up Lambda monitoring with CDK | Use [alarm-template.ts](assets/alarm-template.ts) as a starting point |
| Creating synthetic canaries | Read [synthetics.md](references/synthetics.md) |
| Configuring ADOT collector | Use [otel-config.yaml](assets/otel-config.yaml) as a starting point |
| Spans multiple areas | Read the most specific reference first, then consult others as needed |

## Files

| File | Content |
|------|---------|
| [alarms.md](references/alarms.md) | Metric, composite, anomaly detection alarms — configuration, constraints, recommended defaults |
| [log-insights.md](references/log-insights.md) | Complete query syntax, commands, functions, known issues, reusable query library |
| [metrics.md](references/metrics.md) | Custom metrics, EMF spec, metric filters, high-resolution, retention |
| [tracing.md](references/tracing.md) | X-Ray → ADOT migration, sampling rules, annotations vs metadata, collector config |
| [dashboards.md](references/dashboards.md) | Widget types, cross-account/region, dynamic labels, sharing |
| [troubleshooting.md](references/troubleshooting.md) | Error → cause → fix for all observability services |
| [cloudtrail.md](references/cloudtrail.md) | Operational auditing, event types, S3+Athena queries |
| [synthetics.md](references/synthetics.md) | Canary runtime/blueprint constraints, VPC networking, common failures |
| [alarm-template.ts](assets/alarm-template.ts) | Best-practice CDK Lambda monitoring (alarms + dashboard) |
| [otel-config.yaml](assets/otel-config.yaml) | ADOT collector config for X-Ray traces + CloudWatch EMF metrics |

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
