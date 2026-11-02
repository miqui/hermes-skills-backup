#!/usr/bin/env bash
# REVIEW-ONLY validation template; no resource mutation.
set -euo pipefail

: "${AWS_REGION:?Set AWS_REGION explicitly}"
: "${GATEWAY_ID:?Set GATEWAY_ID explicitly}"

# Verify the exact CLI command and response fields against current AWS docs/CLI help.
aws bedrock-agentcore-control get-gateway \
  --gateway-identifier "$GATEWAY_ID" \
  --region "$AWS_REGION" \
  --output json

echo 'Inspect gateway state, target configuration, IAM/resource policies, logging, and authentication before declaring the deployment healthy.'
