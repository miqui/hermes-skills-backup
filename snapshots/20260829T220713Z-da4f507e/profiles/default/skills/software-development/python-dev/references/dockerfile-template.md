# Python Dockerfile Template Notes

Use this as a starting point for containerized Python services when the repo does not already define a different container strategy.

## Preferred characteristics

- multi-stage build
- slim Python base image
- non-root runtime user
- minimal runtime filesystem contents
- `.dockerignore` present

## Example template

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --compile-bytecode

FROM python:3.11-slim AS runtime

WORKDIR /app

RUN useradd --create-home --uid 1001 appuser

COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv
COPY --chown=appuser:appuser app/ ./app/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Notes

- adjust the final `CMD` to match the real project entrypoint
- if the project is a CLI, use the CLI entrypoint instead of `uvicorn`
- if the project is Lambda-based, use a Lambda-compatible base image and packaging flow
- copy only what the runtime actually needs

## Verification baseline

```bash
hadolint Dockerfile
docker build -t <name>:latest .
```

## Common mistakes

- copying the full repo into runtime when only part is needed
- running as root by default
- forgetting `.dockerignore`
- documenting Docker commands that do not match the actual container entrypoint
