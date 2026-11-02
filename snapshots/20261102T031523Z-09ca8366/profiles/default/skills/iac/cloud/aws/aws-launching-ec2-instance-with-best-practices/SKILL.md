---
name: aws-launching-ec2-instance-with-best-practices
description: "Use when the task involves launching ec2 instances with best practices in AWS. Launches an EC2 instance with secure, cost-efficient defaults including AMI selection, burstable instance sizing, least-privilege IAM roles, hardened security groups, encrypted EBS volumes, and comprehensive tagging. Use when deploying new EC2 instances following AWS best practices for security and cost optimization."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, ec2, compute, security]
    related_skills: [cloud-architect, terraform-infrastructure, aws-setting-up-ec2-instance-profiles]
---

# Launching EC2 Instances with Best Practices

## Overview

This skill covers launching ec2 instances with best practices workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/ec2-skills/launching-ec2-instance-with-best-practices` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-launching-ec2-instance-with-best-practices`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Launch an EC2 instance

To launch a fully configured EC2 instance with best-practice defaults, follow the procedure exactly.
See [EC2 instance launch procedure](references/launch-ec2-instance-with-best-practices.md).

The procedure handles:

- Intelligent defaults based on workload type and environment
- Network validation (VPC, subnet, public/private placement)
- AMI selection with architecture compatibility checks
- Least-privilege IAM roles for required AWS service access
- Hardened security groups with minimal port exposure
- Encrypted gp3 storage with environment-appropriate retention
- Comprehensive tagging for cost tracking and organization
- Post-launch verification and connection instructions

## Troubleshooting

### Insufficient instance capacity

Try a different availability zone or instance type (e.g., t3a instead of t3). See the full troubleshooting guide in the [launch procedure](references/launch-ec2-instance-with-best-practices.md).

### Instance immediately terminates

Check console output with `aws ec2 get-console-output`. Verify EBS volume size is sufficient and AMI is compatible with the instance type.

### Cannot connect via SSH

Verify the security group allows SSH from your IP, key file permissions are `400`, and the instance is running. Consider AWS Systems Manager Session Manager as an alternative.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
