---
name: aws-creating-ec2-image-builder-pipeline
description: "Use when the task involves creating an ec2 image builder pipeline in AWS. Creates a complete EC2 Image Builder pipeline that builds a custom AMI with pre-installed software, distributes it to target regions, executes the pipeline, and creates a launch template. Use when setting up automated AMI creation with IAM roles, build components, image recipes, and infrastructure configuration."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, ec2, image-builder, ami]
    related_skills: [cloud-architect, terraform-infrastructure, aws-launching-ec2-instance-with-best-practices]
---

# Creating an EC2 Image Builder Pipeline

## Overview

This skill covers creating an ec2 image builder pipeline workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/ec2-skills/creating-ec2-image-builder-pipeline` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-creating-ec2-image-builder-pipeline`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Create an Image Builder pipeline

To create a complete EC2 Image Builder pipeline with custom AMI builds and
cross-region distribution, follow the procedure exactly.
See [EC2 Image Builder pipeline procedure](references/ec2-image-builder-pipeline.md).

## Troubleshooting

### InvalidParameterValueException on pipeline operations
Use the exact ARN returned by API calls — do not construct ARNs manually. Pipeline
ARNs must follow `arn:<partition>:imagebuilder:<region>:<account>:image-pipeline/<name>`.

### InstanceProfileNotFoundException
Wait 10–15 seconds after creating the instance profile before using it. IAM changes
are eventually consistent.

### ResourceAlreadyExistsException
Delete the existing resource first or use a different name/version.

### Build instance fails to launch
Verify the instance profile exists, all three IAM policies are attached, and the
instance type is available in the region.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
