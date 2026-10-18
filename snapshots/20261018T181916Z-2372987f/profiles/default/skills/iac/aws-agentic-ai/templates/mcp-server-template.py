#!/usr/bin/env python3
"""Review-only AgentCore MCP server starter for FastMCP 3.x.

The `/mcp` and `/ping` paths, port, transport, and stateless setting are
explicit. Confirm AgentCore's current Runtime contract and the installed
FastMCP version before deployment. `/ping` is deliberately unauthenticated;
it must expose no sensitive application data.
"""

import os

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

PORT = int(os.environ.get("PORT", "8000"))
mcp = FastMCP("AgentCore MCP Template")


@mcp.custom_route("/ping", methods=["GET"])
async def ping(_: Request) -> JSONResponse:
    """Health endpoint; keep this response non-sensitive."""
    return JSONResponse({"status": "Healthy"})


@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two integer values."""
    return a + b


@mcp.tool()
def greet_user(name: str) -> str:
    """Return a simple greeting."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=PORT,
        path="/mcp",
        stateless_http=True,
    )
