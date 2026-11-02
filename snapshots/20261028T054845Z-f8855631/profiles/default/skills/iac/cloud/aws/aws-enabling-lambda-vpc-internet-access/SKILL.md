---
name: aws-enabling-lambda-vpc-internet-access
description: "Use when the task involves enabling lambda vpc internet access in AWS. Enables internet access for AWS Lambda functions deployed in VPC subnets by creating NAT Gateway infrastructure, configuring public/private subnet routing, and updating security groups. Use when a VPC-attached Lambda function cannot reach the internet."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, lambda, vpc, networking]
    related_skills: [cloud-architect, aws-serverless, aws-creating-production-vpc-multi-az]
---

# Enabling Lambda VPC Internet Access

## Overview

This skill covers enabling lambda vpc internet access workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/networking-and-content-delivery-skills/enabling-lambda-vpc-internet-access` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-enabling-lambda-vpc-internet-access`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Enable internet access for a VPC Lambda function

To set up NAT Gateway infrastructure and configure routing for a Lambda function that needs internet access, follow the procedure exactly.
See [Lambda VPC internet access setup procedure](references/lambda-vpc-internet-access.md).

## Troubleshooting

### NAT Gateway not working

Verify the route table associated with the Lambda subnets has a `0.0.0.0/0` route pointing to the NAT Gateway. See the full procedure for details.

### Lambda function timeout

Check that security group outbound rules allow the necessary ports and that both the NAT Gateway and Internet Gateway are properly configured.

### Network changes not taking effect

VPC networking changes can take 1–2 minutes to propagate. Wait before testing after creating a NAT Gateway or updating route tables.

### Route table association issues

Confirm the Lambda function's subnets are associated with the route table that has the `0.0.0.0/0` route to the NAT Gateway.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
