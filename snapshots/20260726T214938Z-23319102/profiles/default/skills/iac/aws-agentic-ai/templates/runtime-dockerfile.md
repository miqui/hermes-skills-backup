# AgentCore Runtime Dockerfile Template

Use this as a review-only starting point. Verify the current AgentCore Runtime container contract, required architecture, and project dependency lock before building.

```dockerfile
FROM public.ecr.aws/docker/library/python:3.12-slim AS builder
WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

FROM public.ecr.aws/docker/library/python:3.12-slim
WORKDIR /app

RUN useradd --create-home --shell /usr/sbin/nologin appuser
COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser . /app

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

# Match this port and entry point to the selected AgentCore Runtime protocol.
EXPOSE 8080
CMD ["uvicorn", "runtime_fastapi_template:app", "--host", "0.0.0.0", "--port", "8080"]
```

Validation before deployment:

- Build for the target architecture.
- Run the image locally and exercise health and representative request paths.
- Scan the image and inspect dependencies.
- Confirm the exposed port, health path, non-root execution, and supported runtime API against current AWS documentation.
