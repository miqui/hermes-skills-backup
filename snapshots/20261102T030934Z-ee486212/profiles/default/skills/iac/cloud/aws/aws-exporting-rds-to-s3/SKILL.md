---
name: aws-exporting-rds-to-s3
description: "Use when the task involves exporting rds/aurora to s3 in AWS. Exports Amazon RDS or Aurora database snapshots to Amazon S3 in Apache Parquet format for analytics, backup, or data migration. Handles snapshot selection or creation, IAM role setup, KMS encryption, S3 bucket preparation, export task execution, progress monitoring, and data verification. Use when exporting RDS/Aurora data to S3 for Athena, Glue, or Redshift Spectrum consumption."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, rds, s3, export]
    related_skills: [cloud-architect, terraform-infrastructure, aws-securing-s3-buckets]
---

# Exporting RDS/Aurora to S3

## Overview

This skill covers exporting rds/aurora to s3 workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/database-skills/exporting-rds-to-s3` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-exporting-rds-to-s3`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Export an RDS or Aurora snapshot to S3

To export a database snapshot to S3 with proper IAM roles, encryption, and monitoring,
follow the procedure exactly.
See [RDS to S3 export procedure](references/export-rds-to-s3.md).

## Troubleshooting

### Database not found
Verify the database identifier spelling, case, and region. For Aurora, use `describe-db-clusters` instead of `describe-db-instances`.

### Export not supported
Snapshot export supports MySQL, PostgreSQL, MariaDB, Aurora MySQL, and Aurora PostgreSQL only. Oracle and SQL Server are not supported.

### IAM role permission errors
Ensure the role trust policy allows `export.rds.amazonaws.com` with `aws:SourceAccount` and `aws:SourceArn` conditions for confused deputy protection, and has S3 PutObject and KMS permissions. Wait 10–15 seconds after role creation for propagation.

### Export stuck or failed
Check the export task status for failure reasons. Common causes: S3 bucket deleted, IAM role modified, or KMS key disabled during export. See the [full procedure](references/export-rds-to-s3.md) for detailed troubleshooting.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
