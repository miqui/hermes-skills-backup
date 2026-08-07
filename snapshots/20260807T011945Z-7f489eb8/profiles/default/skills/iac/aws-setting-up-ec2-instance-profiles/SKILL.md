---
name: aws-setting-up-ec2-instance-profiles
description: "Use when the task involves setting up ec2 instance profiles in AWS. Configures EC2 instances to securely call AWS services by creating and attaching IAM roles via instance profiles, eliminating hardcoded credentials. Use when an EC2 instance needs permissions to access AWS services like S3, DynamoDB, SQS, or CloudWatch through temporary credentials."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, ec2, iam, instance-profiles]
    related_skills: [cloud-architect, aws-iam, aws-launching-ec2-instance-with-best-practices]
---

# Setting Up EC2 Instance Profiles

## Overview

This skill covers setting up ec2 instance profiles workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/ec2-skills/setting-up-ec2-instance-profiles` into Hermes-native skill format for the local `iac` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-setting-up-ec2-instance-profiles`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Configure an EC2 instance profile

To set up an IAM role and instance profile for an EC2 instance, follow the procedure exactly.
See [EC2 instance profile setup procedure](references/ec2-instance-profile-setup.md).

## Troubleshooting

### Instance not found

Verify the instance ID and region are correct. List instances with `aws ec2 describe-instances --region <region>`.

### Instance already has a profile

The procedure handles replacement — it will prompt before disassociating the existing profile.

### Credentials not available after attachment

Instance profile propagation can take 30–60 seconds. Applications may need a restart to pick up new credentials.

### Access denied errors

Check that the role's policies include the required actions and resource ARNs. Review CloudTrail logs for the specific denied action.

### Application still uses hardcoded credentials

Remove credentials from config files, environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`), and `~/.aws/credentials`. The SDK default credential chain will then use the instance profile.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
