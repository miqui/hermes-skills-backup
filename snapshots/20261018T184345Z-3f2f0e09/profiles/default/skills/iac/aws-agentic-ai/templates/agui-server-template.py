#!/usr/bin/env python3
"""Review-only AgentCore AG-UI server starter.

Confirm the current AG-UI and Strands APIs, required Runtime protocol settings,
and authentication behavior before deployment.
"""

import logging
import os

import uvicorn
from ag_ui.core import RunAgentInput
from ag_ui.encoder import EventEncoder
from ag_ui_strands import StrandsAgent
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from strands import Agent
from strands.models.bedrock import BedrockModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model_id = os.environ.get("MODEL_ID")
aws_region = os.environ.get("AWS_REGION")
if not model_id:
    raise RuntimeError("Set MODEL_ID to a model or inference-profile ID verified for the target region")
if not aws_region:
    raise RuntimeError("Set AWS_REGION explicitly; do not rely on an implicit region default")

model = BedrockModel(
    model_id=model_id,
    region_name=aws_region,
)

strands_agent = Agent(model=model, system_prompt="You are a helpful assistant.")
agui_agent = StrandsAgent(
    agent=strands_agent,
    name="my_agent",
    description="A helpful assistant",
)

app = FastAPI()


@app.post("/invocations")
async def invocations(input_data: dict, request: Request):
    encoder = EventEncoder(accept=request.headers.get("accept"))
    try:
        run_input = RunAgentInput(**input_data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid input: {exc}") from exc

    async def event_generator():
        try:
            async for event in agui_agent.run(run_input):
                yield encoder.encode(event)
        except Exception:
            logger.exception("AG-UI streaming error")
            raise

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())


@app.get("/ping")
async def ping():
    return {"status": "Healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
