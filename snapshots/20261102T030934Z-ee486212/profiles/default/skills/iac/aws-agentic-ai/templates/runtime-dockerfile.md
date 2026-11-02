# AgentCore Runtime Dockerfile Template

Use this as a review-only starting point. It intentionally has **no default base image**: supply a verified digest at build time so the build is reproducible.

```dockerfile
# Example invocation (substitute a verified digest from your approved registry):
# docker build \
#   --build-arg PYTHON_BASE_IMAGE='public.ecr.aws/docker/library/python@sha256:<verified-digest>' \
#   -t agentcore-runtime:local .
ARG PYTHON_BASE_IMAGE
FROM ${PYTHON_BASE_IMAGE} AS builder
WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt ./
# requirements.txt must be an approved, hash-locked dependency file.
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

FROM ${PYTHON_BASE_IMAGE}
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

- Build with an approved, pinned image digest; do not substitute a floating tag.
- Use a hash-locked `requirements.txt`; do not add package upgrades during image build.
- Build for the target architecture.
- Run the image locally and exercise health and representative request paths.
- Scan the image and inspect dependencies.
- Confirm the exposed port, health path, non-root execution, and supported runtime API against current AWS documentation.
