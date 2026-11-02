# Minimal FastAPI Starter Layout

Use this as the **smallest sensible starting point** for a new FastAPI service when the repository does not already define a different structure.

This file is intentionally lightweight. It should help with greenfield setup without duplicating the deeper guidance in `references/fastapi-production-patterns.md`.

If the service quickly needs auth, database wiring, repository/service layers, or more formal dependency boundaries, keep the same naming direction and then expand using `references/fastapi-production-patterns.md`.

## Starter layout

```text
project/
  app/
    api/
      router.py
      routes/
        health.py
    core/
      config.py
    main.py
  tests/
    test_health.py
  pyproject.toml
  .env.example
  README.md
```

## Layout notes

- `app/main.py` creates the FastAPI app and includes the top-level API router.
- `app/api/router.py` gathers route modules into a single router.
- `app/api/routes/` holds route handlers.
- `app/core/config.py` holds app settings and shared configuration wiring.
- `tests/` should contain at least one startup or route-level smoke test.

This starter intentionally omits service, repository, and database layers. Add them when the application complexity justifies them, not preemptively.

## Main app pattern

```python
from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(title="Example Service", version="0.1.0")
app.include_router(api_router)
```

## Router aggregation pattern

```python
from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router)
```

## Route pattern

```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get("", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")
```

## Minimal settings pattern

Use a tiny settings module only if the starter actually needs configuration.

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "example-service"
    api_v1_prefix: str = "/api/v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

## Testing baseline

Prefer a simple async route test using modern `httpx` transport wiring.

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_healthcheck() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

## When to expand beyond this starter

Move to `references/fastapi-production-patterns.md` when you need any of the following:

- app lifespan wiring
- authentication and authorization
- database sessions
- SQLAlchemy models and repositories
- service-layer business logic
- centralized exception handling
- more structured integration and unit tests

## FastAPI starter pitfalls

1. **Starting with too much architecture.** Do not add repositories, services, and database layers before the app needs them.
2. **Using inconsistent names between starter and grown-up layouts.** Start with `api/router.py` and `api/routes/` so expansion is straightforward.
3. **Skipping tests even for a tiny app.** A simple health-route test is enough to validate startup and routing.
4. **Adding config machinery before you need config.** Keep `core/config.py` tiny until real settings appear.
5. **Copying outdated examples.** Prefer current FastAPI, Pydantic v2, and `httpx` transport patterns in new code.
