---
name: fastmcp-http-python-docker-server
description: Scaffold a FastMCP server exposed over streamable HTTP with env-based secrets, uv-based local runtime, tests, and hardened Docker assets.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mcp, fastmcp, python, docker, uv, streamable-http]
---

# FastMCP HTTP Python + Docker Server

## When to Use

Use when creating a new FastMCP server that should:
- expose tools over `streamable-http`
- read API keys from environment variables
- support both local Python and Docker runtime paths
- include minimal tests and a README

## Workflow

1. Create the project under `/Users/miqui/development/<repo-name>` on this host.
2. Initialize git locally immediately.
3. Prefer Python 3.11+ with `uv`, even if `/usr/bin/python3` is older.
4. Create a package layout under `src/<package_name>/`.
5. Add:
   - `pyproject.toml`
   - `.env.example`
   - `.gitignore`
   - `.dockerignore`
   - `README.md`
   - `run_server.py`
   - `scripts/run-local.sh`
   - `scripts/run-docker.sh`
   - `tests/`
6. Install FastMCP into a local venv and introspect the installed API instead of guessing method names/signatures.
7. For FastMCP 3.x, use `mcp.run(transport="streamable-http", host=..., port=..., path=..., stateless_http=...)`.
8. Verify with:
   - `uv pip install -e '.[dev]'`
   - `pytest`
   - a smoke import such as `mcp.http_app(path='/mcp', stateless_http=False)`
9. If the upstream API has a large or ambiguous parameter surface, validate documented parameter names/values before expanding the request model.
10. If Docker is unavailable on the host, still scaffold Docker assets and explicitly note they were not build-tested.

## FastMCP 3.x Notes

- The package name is `fastmcp` on PyPI and currently requires Python `>=3.10`.
- On hosts where `/usr/bin/python3` is older, use `uv` to create a Python 3.11+ virtualenv instead of forcing the system interpreter.
- Verify the installed transport surface directly. In this session, `FastMCP` exposed `run(...)`, `run_http_async(...)`, and `http_app(...)`, while `run_streamable_http(...)` was not present.

## Docker Hardening Notes

For the Docker path, prefer:
- multi-stage builds
- non-root runtime user with fixed UID/GID when practical
- `PIP_NO_CACHE_DIR=1`
- minimal runtime packages only
- a read-only runtime invocation plus `tmpfs /tmp` in helper scripts when the service can tolerate it

See `references/serpapi-google-flights-params.md` for a concise parameter set validated during a Google Flights server scaffold.

## Implementation Notes

- Keep secrets out of source; use env vars like `SERPAPI_API_KEY`.
- Wrap upstream API access in a dedicated client module.
- Raise clear errors for missing env vars and upstream HTTP failures.
- Return a structured subset of the upstream payload plus the raw payload when useful.
- Add a lightweight `health_check` tool.
- Use a multi-stage Docker build and run as non-root.

## Common Pitfalls

- Assuming the host default Python is sufficient for FastMCP
- Guessing FastMCP transport APIs without checking installed signatures
- Hardcoding API keys in code or examples
- Claiming Docker verification when Docker is not installed
