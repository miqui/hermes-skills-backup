---
name: aws-creating-amazon-aurora-db-cluster-with-instances
description: "Use when the task involves creating amazon aurora db cluster with instances in AWS. Creates a complete Amazon Aurora database cluster with instances, handling cluster creation, instance provisioning, and Secrets Manager password management in the proper sequence. Use when setting up new Aurora MySQL or PostgreSQL clusters with production-ready configuration."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, aurora, rds, database]
    related_skills: [cloud-architect, terraform-infrastructure, aws-exporting-rds-to-s3]
---

# Creating Amazon Aurora DB Cluster with Instances

## Overview

This skill covers creating amazon aurora db cluster with instances workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/database-skills/creating-amazon-aurora-db-cluster-with-instances` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-creating-amazon-aurora-db-cluster-with-instances`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Create an Aurora cluster with instances

To create a fully configured Aurora database cluster with attached instances,
follow the procedure exactly.
See [Aurora cluster creation procedure](references/create-amazon-aurora-db-cluster-with-instances.md).

The procedure creates an empty Aurora cluster first, then adds a database instance
to make it queryable. It uses AWS Secrets Manager for password management and
includes proper status monitoring with retry logic.

## Troubleshooting

### Cluster creation fails

Verify the engine version is supported in your region and that you have sufficient
permissions for RDS and Secrets Manager operations.

### Instance creation fails

Check that the instance class is compatible with the Aurora engine and available
in your region's availability zones.

### Long creation times

Aurora cluster and instance creation can take 10-20 minutes. Extended wait times
are normal for Aurora resources.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
