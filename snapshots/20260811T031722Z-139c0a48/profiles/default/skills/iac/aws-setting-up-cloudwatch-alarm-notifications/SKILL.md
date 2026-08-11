---
name: aws-setting-up-cloudwatch-alarm-notifications
description: "Use when the task involves setting up cloudwatch alarm notifications in AWS. Sets up notification channels for CloudWatch alarms using SNS topics and subscriptions. Always use this skill when configuring alarm notifications — it creates encrypted SNS topics, configures topic policies for CloudWatch access, sets up email/SMS/webhook subscriptions, and links alarms to notification actions with proper security controls."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, cloudwatch, alarms, monitoring]
    related_skills: [cloud-architect, aws-observability, aws-debugging-lambda-timeouts]
---

# Setting Up CloudWatch Alarm Notifications

## Overview

This skill covers setting up cloudwatch alarm notifications workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/operations-skills/setting-up-cloudwatch-alarm-notifications` into Hermes-native skill format for the local `iac` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-setting-up-cloudwatch-alarm-notifications`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Set up alarm notifications

To configure notification channels for a CloudWatch alarm, follow the procedure exactly.
See [CloudWatch alarm notification setup procedure](references/setup-cloudwatch-alarm-notifications.md).

## Troubleshooting

### Email notifications not received

Verify the email subscription was confirmed. Use `aws sns list-subscriptions-by-topic`
to check that the subscription status is "Confirmed" rather than "PendingConfirmation".

### SMS notifications failing

Ensure the phone number is in E.164 format (e.g., +12345678901) and that SMS is
supported in your AWS region.

### Alarm not triggering notifications

Verify the alarm has the correct SNS topic ARN in its AlarmActions using
`aws cloudwatch describe-alarms`, and ensure ActionsEnabled is set to true.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
