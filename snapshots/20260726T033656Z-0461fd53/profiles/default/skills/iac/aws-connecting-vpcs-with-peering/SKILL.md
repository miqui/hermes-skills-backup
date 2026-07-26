---
name: aws-connecting-vpcs-with-peering
description: "Use when the task involves connecting vpcs with peering in AWS. Establishes VPC peering connections between two VPCs for direct private network connectivity. Always use this skill when creating or managing VPC peering — it validates CIDR overlap, updates all route tables in both VPCs, configures DNS resolution, and provides security group guidance that are critical for correct connectivity."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, vpc, peering, networking]
    related_skills: [cloud-architect, terraform-infrastructure, aws-creating-production-vpc-multi-az]
---

# Connecting VPCs with Peering

## Overview

This skill covers connecting vpcs with peering workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/networking-and-content-delivery-skills/connecting-vpcs-with-peering` into Hermes-native skill format for the local `iac` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-connecting-vpcs-with-peering`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Create a VPC peering connection

To establish a VPC peering connection between two VPCs, follow the procedure exactly.
See [VPC peering connection procedure](references/vpc-peering-connection.md).

The procedure requires the requester and accepter VPC IDs at minimum. It validates both VPCs exist, checks for CIDR overlap, creates and accepts the peering, updates all route tables, and configures DNS resolution.

## Troubleshooting

### Peering stuck in pending state

Cross-account connections require manual acceptance from the accepter account. Same-account connections with `auto_accept: true` should transition automatically.

### Route creation fails

Check for existing routes with the same destination CIDR. Replace existing routes instead of creating new ones.

### DNS resolution not working

Both VPCs must have DNS resolution and DNS hostnames enabled in their VPC settings, not just the peering connection options.

### Cross-region connectivity issues

Verify routes are added in both regions and security groups allow traffic from the peer VPC's CIDR blocks.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
