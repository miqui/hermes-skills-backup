---
name: aws-configuring-vpc-endpoints-for-private-aws-service-access
description: "Use when the task involves configuring vpc endpoints for private aws service access in AWS. Configures VPC endpoints (interface and gateway) for private AWS service access using AWS PrivateLink. Use when setting up secure private connectivity to S3, DynamoDB, and other AWS services without internet gateway, NAT device, or public IP addresses. Covers endpoint creation, security groups, route tables, and DNS configuration."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, vpc, private-connectivity, endpoints]
    related_skills: [cloud-architect, terraform-infrastructure, aws-creating-production-vpc-multi-az]
---

# Configuring VPC Endpoints for Private AWS Service Access

## Overview

This skill covers configuring vpc endpoints for private aws service access workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/networking-and-content-delivery-skills/configuring-vpc-endpoints-for-private-aws-service-access` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-configuring-vpc-endpoints-for-private-aws-service-access`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Configure VPC endpoints

To create and configure VPC endpoints for private AWS service access, follow the procedure exactly.
See [VPC endpoints configuration procedure](references/configure-vpc-endpoints-for-private-aws-service-access.md).

## Troubleshooting

### Endpoint not available

Check security group rules, subnet configurations, and service availability in the region.

### DNS resolution issues

Verify DNS hostnames and DNS resolution are enabled on the VPC and that the DHCP options set has correct domain name servers.

### Connection timeouts

Verify security group rules allow HTTPS traffic (port 443) and route tables are properly configured for gateway endpoints.

### Policy restrictions

Review endpoint policies — default policies allow all access, but custom policies may be restrictive.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
