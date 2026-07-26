#!/usr/bin/env python3
"""Review-only AgentCore MCP server starter.

Verify FastMCP's current API, AgentCore's required port/health contract, and
MCP authorization requirements before deploying this example.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(host="0.0.0.0", stateless_http=True)


@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two integer values."""
    return a + b


@mcp.tool()
def greet_user(name: str) -> str:
    """Return a simple greeting."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    # Validate current FastMCP transport and port configuration before use.
    mcp.run(transport="streamable-http")
