#!/usr/bin/env python3
"""Review-only AgentCore HTTP Runtime starter (FastAPI).

Before deployment, verify the selected AgentCore Runtime protocol contract,
current Strands/MCP APIs, model/inference-profile availability, CORS origin,
and authentication design. This template requires MODEL_ID explicitly so a
stale model default is not silently deployed.
"""

import json
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from strands import Agent
from strands.models.bedrock import BedrockModel
from strands.tools.mcp import MCPClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_ID = os.environ.get("MODEL_ID")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", "You are a helpful AI assistant.")
AWS_REGION = os.environ.get("AWS_REGION")

if not MODEL_ID:
    raise RuntimeError("Set MODEL_ID to a model or inference-profile ID verified for the target region")
if not AWS_REGION:
    raise RuntimeError("Set AWS_REGION explicitly; do not rely on an implicit region default")


class MessagePart(BaseModel):
    type: str = "text"
    text: str


class Message(BaseModel):
    id: str = ""
    role: str
    content: str
    parts: list[MessagePart] = Field(default_factory=list)


class ChatRequest(BaseModel):
    id: str
    user_id: str = ""
    messages: list[Message] = Field(default_factory=list)


model = BedrockModel(model_id=MODEL_ID, region_name=AWS_REGION)
_mcp_client: MCPClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    global _mcp_client
    if MCP_SERVER_URL:
        try:
            from mcp.client.streamable_http import streamable_http_client

            _mcp_client = MCPClient(lambda: streamable_http_client(url=MCP_SERVER_URL))
            logger.info("MCP client initialized")
        except Exception:
            logger.exception("Failed to initialize the configured MCP client")
            raise
    yield
    if _mcp_client:
        try:
            await _mcp_client.close()
        except Exception:
            logger.exception("Error closing MCP client")


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    # Confirm the actual permitted origin(s) for the deployment; do not use '*'
    # with credentials.
    allow_origins=[f"https://bedrock-agentcore.{AWS_REGION}.amazonaws.com"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["content-type", "authorization"],
)


@app.get("/ping")
def ping():
    return {"status": "Healthy"}


@app.post("/invocations")
async def invocations(request: ChatRequest):
    user_message = request.messages[-1].content if request.messages else ""
    agent = Agent(
        system_prompt=SYSTEM_PROMPT,
        model=model,
        tools=[_mcp_client] if _mcp_client else [],
    )

    async def event_generator():
        yield f"data: {json.dumps({'type': 'start', 'session_id': request.id})}\n\n"
        try:
            async for event in agent.stream_async(user_message):
                text = event.get("data", "") if isinstance(event, dict) else ""
                if text:
                    yield f"data: {json.dumps({'type': 'text-delta', 'delta': text})}\n\n"
            yield f"data: {json.dumps({'type': 'finish', 'session_id': request.id})}\n\n"
        except Exception:
            logger.exception("Streaming error for session %s", request.id)
            # Avoid returning raw upstream error details to a caller.
            yield f"data: {json.dumps({'type': 'error', 'message': 'Request processing failed'})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
