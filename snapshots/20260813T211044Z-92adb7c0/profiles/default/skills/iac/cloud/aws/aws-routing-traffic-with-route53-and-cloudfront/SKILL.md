---
name: aws-routing-traffic-with-route53-and-cloudfront
description: "Use when the task involves routing traffic with route 53 and cloudfront in AWS. Configures Amazon Route 53 to route traffic to a CloudFront distribution using a custom domain. Use when setting up DNS alias records, alternate domain names (CNAMEs), ACM certificates for HTTPS, and IPv6 support for CloudFront."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [aws, iac, route53, cloudfront, dns, cdn]
    related_skills: [cloud-architect, terraform-infrastructure, aws-creating-production-vpc-multi-az]
---

# Routing Traffic with Route 53 and CloudFront

## Overview

This skill covers routing traffic with route 53 and cloudfront workflows in AWS and was adapted from `aws/agent-toolkit-for-aws/specialized-skills/networking-and-content-delivery-skills/routing-traffic-with-route53-and-cloudfront` into Hermes-native skill format for the local `iac/cloud/aws` taxonomy.

## When to Use

- Use this skill when the task matches the AWS scope described by `aws-routing-traffic-with-route53-and-cloudfront`.
- Start with the most specific linked reference or asset in this skill directory before broad web searching.
- Verify mutable AWS facts such as quotas, runtime versions, CLI behavior, and regional availability against current AWS documentation when precision matters.

## Configure Route 53 to route traffic to a CloudFront distribution

To set up a custom domain for a CloudFront distribution with Route 53 DNS, follow the procedure exactly.
See [Route 53 CloudFront routing procedure](references/route53-cloudfront-routing.md).

The procedure covers:

- Verifying CloudFront distribution status and CNAME configuration
- Requesting and validating ACM certificates (must be in us-east-1)
- Creating or locating public hosted zones
- Creating alias A and AAAA records pointing to CloudFront
- Monitoring DNS propagation

## Troubleshooting

### Domain not in CloudFront CNAMEs

Add the domain as an alternate domain name in the CloudFront distribution configuration before creating Route 53 records.

### SSL certificate issues

ACM certificates for CloudFront must be in us-east-1. Ensure the certificate is validated and associated with the distribution.

### Private hosted zone

CloudFront only works with public hosted zones. Create a public hosted zone if only a private one exists.

### DNS propagation delays

Changes typically propagate within 60 seconds but full global propagation can take up to 48 hours. Use `nslookup` or `dig` to verify.

## Common Pitfalls

1. Treating upstream examples, versions, quotas, or region-specific behaviors as timeless facts without checking current AWS documentation.
2. Using a broad AWS approach when a more specific linked reference in this skill directory addresses the exact service or failure mode.
3. Applying this skill outside its AWS scope when an existing peer skill such as `cdk-patterns`, `terraform-infrastructure`, or `cloud-architect` is the better fit.

## Verification Checklist

- [ ] The task matches this skill's AWS service or workflow scope
- [ ] The most relevant linked reference or asset in this directory was reviewed first
- [ ] Time-sensitive AWS details were verified against current documentation when needed
- [ ] Any infrastructure or production-impacting change was validated before rollout
