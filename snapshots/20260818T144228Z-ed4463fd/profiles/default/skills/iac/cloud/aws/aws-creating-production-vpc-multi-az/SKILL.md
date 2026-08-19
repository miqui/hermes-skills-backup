---
name: aws-creating-production-vpc-multi-az
description: "Use when the task involves creating a production-ready vpc across multiple availability zones in AWS. Creates a production-ready VPC with public and private subnets across multiple Availability Zones, including internet gateway, NAT gateways, route tables, and security groups following AWS Well-Architected principles. Use when deploying multi-AZ VPC infrastructure with automatic CIDR planning and DNS resolution."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, vpc, multi-az, networking]
    related_skills: [cloud-architect, terraform-infrastructure, aws-connecting-vpcs-with-peering]
---

# Creating a Production-Ready VPC Across Multiple Availability Zones

## Overview

This skill covers creating a production-ready vpc across multiple availability zones workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/networking-and-content-delivery-skills/creating-production-vpc-multi-az` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-creating-production-vpc-multi-az`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Create a production VPC

To create a fully configured multi-AZ VPC with public/private subnets, NAT gateways,
route tables, and security groups, follow the procedure exactly.
See [Production VPC creation procedure](references/create-production-vpc-multi-az.md).

Key parameters:

- `vpc_name` (required): Name prefix for all resources
- `region` (required): Target AWS region
- `allowed_web_cidrs` (required): CIDR blocks allowed for web access — allow 0.0.0.0/0 only if explicitly requested
- `vpc_cidr` (optional, default `10.0.0.0/16`): VPC CIDR block
- `availability_zones` (optional, default 3): Number of AZs (2–6)
- `environment` (required): Environment tag
- `enable_ssh_access` (optional, default false): Whether to create SSH security group

## Troubleshooting

### Insufficient Availability Zones

The target region must have at least 2 available AZs. Use `aws ec2 describe-availability-zones` to verify.

### NAT Gateway creation delays

NAT Gateways can take several minutes to become available. The procedure waits for availability before configuring route tables.

### Security group CIDR warnings

The procedure warns about `0.0.0.0/0` for web access CIDRs and recommends specific IP ranges for production workloads, but allows it if explicitly requested.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
