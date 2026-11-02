#!/usr/bin/env python3
"""Review-only CDK custom-resource Lambda template for AgentCore Gateway.

This source-derived pattern creates, replaces, and deletes a Gateway/target.
Validate every boto3 operation, request field, asynchronous state, and
CloudFormation response dependency against the current service model before
using it. Prefer native CDK L1/L2 support when available.

`cfnresponse` is not a general PyPI dependency. Bundle an approved response
helper with the Lambda artifact/layer, or replace it with a reviewed response
implementation before packaging this template.
"""

import logging
import os
import time

import boto3
import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)
client = boto3.client("bedrock-agentcore-control")


def handler(event, context):
    request_type = event["RequestType"]
    try:
        if request_type == "Create":
            result = handle_create()
        elif request_type == "Update":
            result = handle_update(event)
        elif request_type == "Delete":
            result = handle_delete(event)
        else:
            raise ValueError(f"Unknown RequestType: {request_type}")

        physical_id = result.get("GatewayId", event.get("PhysicalResourceId", ""))
        cfnresponse.send(event, context, cfnresponse.SUCCESS, result, physical_id)
    except Exception:
        logger.exception("Custom resource %s failed", request_type)
        physical_id = event.get("PhysicalResourceId", f"failed-{context.aws_request_id}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, physical_id)


def handle_create():
    gateway_name = os.environ["GATEWAY_NAME"]
    target_lambda_arn = os.environ["TARGET_LAMBDA_ARN"]
    schema_s3_uri = os.environ["OPENAPI_SCHEMA_S3_URI"]
    gateway_role_arn = os.environ["GATEWAY_IAM_ROLE_ARN"]

    response = client.create_gateway(
        name=gateway_name,
        protocolType="MCP",
        description=f"Gateway for {gateway_name}",
    )
    gateway_id = response["gatewayId"]
    logger.info("Created Gateway: %s", gateway_id)

    try:
        wait_for_gateway_available(gateway_id)
        target_response = client.create_gateway_target(
            gatewayIdentifier=gateway_id,
            name=f"{gateway_name}-target",
            targetConfiguration={
                "lambdaTargetConfiguration": {
                    "lambdaArn": target_lambda_arn,
                    "roleArn": gateway_role_arn,
                }
            },
            schemaConfiguration={"s3": {"uri": schema_s3_uri}},
            description="Lambda target",
        )
    except Exception:
        logger.exception("Gateway creation follow-up failed; attempting cleanup: %s", gateway_id)
        _delete_gateway(gateway_id)
        raise

    return {"GatewayId": gateway_id, "TargetId": target_response.get("targetId", "")}


def handle_update(event):
    old_gateway_id = event.get("PhysicalResourceId", "")
    result = handle_create()
    if old_gateway_id:
        try:
            _delete_gateway(old_gateway_id)
        except Exception:
            logger.exception("Old gateway cleanup failed; manual review required")
    return result


def handle_delete(event):
    gateway_id = event.get("PhysicalResourceId", "")
    if not gateway_id or gateway_id.startswith("failed-"):
        return {"Status": "Nothing to delete"}
    _delete_gateway(gateway_id)
    return {"Status": "Deleted"}


def _delete_gateway(gateway_id):
    try:
        targets = client.list_gateway_targets(gatewayIdentifier=gateway_id)
        for target in targets.get("gatewayTargets", []):
            try:
                client.delete_gateway_target(
                    gatewayIdentifier=gateway_id,
                    targetIdentifier=target["targetId"],
                )
            except client.exceptions.ResourceNotFoundException:
                pass
        client.delete_gateway(gatewayIdentifier=gateway_id)
        logger.info("Deleted Gateway: %s", gateway_id)
    except client.exceptions.ResourceNotFoundException:
        logger.info("Gateway already deleted: %s", gateway_id)


def wait_for_gateway_available(gateway_id, timeout=300, interval=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get_gateway(gatewayIdentifier=gateway_id)
        status = response.get("status", "")
        if status == "AVAILABLE":
            return
        if status in ("FAILED", "DELETED"):
            raise RuntimeError(f"Gateway {gateway_id} entered terminal state: {status}")
        logger.info("Gateway %s status: %s", gateway_id, status)
        time.sleep(interval)
    raise TimeoutError(f"Gateway {gateway_id} did not become available within {timeout}s")
