#!/usr/bin/env bash
# REVIEW-ONLY TEMPLATE. It deliberately validates/synthesizes rather than deploys.
# Use project-specific CDK commands after explicit approval and a reviewed diff.
set -euo pipefail

: "${AWS_REGION:?Set AWS_REGION explicitly}"
: "${CDK_APP:?Set CDK_APP to the project CDK app command/path}"

printf 'Region: %s\n' "$AWS_REGION"
printf 'CDK app: %s\n' "$CDK_APP"

# Examples; adapt to the project and run from its repository root.
# npx cdk synth --app "$CDK_APP"
# npx cdk diff --app "$CDK_APP" --context region="$AWS_REGION"

echo 'No deployment was performed. Review synth/diff output, IAM/resource policies, and obtain approval before cdk deploy.'
