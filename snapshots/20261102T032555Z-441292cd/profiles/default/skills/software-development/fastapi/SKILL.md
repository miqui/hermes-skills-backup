---
name: fastapi
description: "Use when building, testing, reviewing, or deploying FastAPI services: routers, Pydantic v2 schemas, dependencies, lifespan, settings, testing, OpenAPI, uvicorn/containers, Cloud Run + Firestore."
version: '1.0'
metadata:
  hermes:
    tags: [fastapi, python, pydantic, asgi, uvicorn, rest-api, async]
    related_skills: [python-dev, python-observability, openapi-specification, application-authorization, aws-agentic-ai, test-driven-development]
---

# FastAPI

Consolidates the FastAPI guidance previously split across `python-dev/references/fastapi-layout.md`, `fastapi-production-patterns.md`, and `fastapi-cloudrun-firestore.md`, re-checked against primary docs.

**Verification status.** Verified against fastapi.tiangolo.com on 2026-11-01: latest release listed in the release notes was **FastAPI 0.162.0 (2026-10-23)**. Pydantic docs checked: `pydantic-settings` page (docs.pydantic.dev now redirects to pydantic.dev/docs/validation/latest/...); **exact Pydantic / pydantic-settings / Starlette versions were not stated on the pages fetched -> UNVERIFIED**. Claims marked `UNVERIFIED` came from the old references or memory and were not confirmed on a primary page. Re-check `fastapi --version` / `uv pip list` in the target repo.

## When to use

- New FastAPI service, or adding endpoints/routers/dependencies to one.
- Modernizing to Pydantic v2, lifespan, `Annotated` dependencies, async tests.
- Reviewing/deploying (uvicorn, Docker, Cloud Run).

Do NOT restructure a repo that already has a coherent layout unless asked. `python-dev` stays primary for repo inspection, `uv`, ruff/mypy, README/Docker expectations; this skill adds FastAPI-specific depth.

## Project layout

Start minimal; grow only when complexity justifies it. Official multi-file layout (https://fastapi.tiangolo.com/tutorial/bigger-applications/): `app/__init__.py`, `main.py`, `dependencies.py`, `routers/{items,users}.py`, `internal/admin.py`.

Starter (greenfield, no DB):

```text
project/
  app/
    api/router.py          # aggregates routers
    api/routes/health.py
    core/config.py         # settings
    main.py                # creates FastAPI(), include_router
  tests/test_health.py
  pyproject.toml  .env.example  README.md
```

Grown service (add layers only when needed):

```text
app/
  api/{dependencies.py, router.py, routes/{auth,health,users}.py}
  core/{config,database,logging,security,exceptions}.py
  db/{base.py, models/user.py}
  repositories/user_repository.py
  schemas/{auth,user}.py
  services/{auth_service,user_service}.py
  main.py
tests/{integration,unit}/
```

- `api/routes/`: HTTP only (parsing, response models, status codes, auth requirements).
- `services/`: business rules; `repositories/`: persistence queries; `core/`: app-wide wiring.
- `api/dependencies.py`: request-time dependencies, no business logic.
- Keep names consistent between starter and grown layout (`api/router.py`, `api/routes/`) so expansion is a move, not a rewrite.

```python
# app/main.py
from fastapi import FastAPI
from app.api.router import api_router
app = FastAPI(title="Example Service", version="0.1.0")
app.include_router(api_router)

# app/api/router.py
from fastapi import APIRouter
from app.api.routes import health
api_router = APIRouter()
api_router.include_router(health.router)
```

Verified router facts (bigger-applications page):
- `APIRouter(prefix=..., tags=..., dependencies=[Depends(...)], responses=...)`; the prefix must not end with `/`.
- Order of dependency execution: router dependencies -> decorator `dependencies` -> parameter dependencies.
- `include_router(router, prefix=, tags=, dependencies=, responses=)` customizes a router you cannot edit; the same router may be included several times with different prefixes; routers can include routers.
- Import submodules (`from .routers import items, users`), not both `router` names, to avoid collisions.
- Don't mutate `router.routes` after inclusion; use decorators / `include_router`.
- Entrypoint can be set in `pyproject.toml`: `[tool.fastapi] entrypoint = "app.main:app"`, then `uv run fastapi dev`.

## Pydantic v2 models & validation

```python
from pydantic import BaseModel, ConfigDict, EmailStr   # EmailStr needs email-validator extra (UNVERIFIED here)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
```

- Separate input (`UserCreate`) and output (`UserRead`) schemas; never return ORM objects without a response schema.
- v2 idioms: `model_dump()`, `model_validate()`, `ConfigDict`, `SettingsConfigDict` (not `.dict()`, `class Config`).
- Prefer a return-type annotation or `response_model=` on routes (https://fastapi.tiangolo.com/tutorial/response-model/).
- Pydantic `Field()` metadata is preserved on request params (release notes 0.154-0.156). Use `json_schema_extra={...}` for extra schema props; the old `**extra` kwargs on `Query/Path/Body/...` were removed in 0.155 (TypeError).
- Behavior changes in recent releases (https://fastapi.tiangolo.com/release-notes/): 0.148 omitted `Query/Header/Cookie/Form` defaults are not validated unless `validate_default=True`; 0.151 JSON `null` is distinguished from an omitted body value; 0.162 omitted `bool` form fields no longer inferred `False` (declare default `False` for checkboxes). Query/header/cookie/form parameter models apply `extra` config to all submitted fields in that location (0.160).

## Dependency injection

```python
from typing import Annotated
from fastapi import Depends

def get_user_service(session: Annotated[AsyncSession, Depends(get_db_session)]) -> UserService:
    return UserService(UserRepository(session))

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
```

- Prefer `Annotated[T, Depends(...)]` (docs mark non-Annotated variants "prefer Annotated").
- Good dependency uses: current principal, DB session, pagination/filter parsing, cheap service construction. Avoid hiding business decisions in dependencies or building a pseudo-DI framework.
- `yield` dependencies (https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/), verified:
  - yield exactly once; works with sync or async; sub-dependency exit code runs in correct order.
  - Exit code runs **after the response is sent** by default (`scope="request"`). `Depends(fn, scope="function")` closes it after the path function returns but before the response is sent.
  - If you `except` inside a yield dependency and don't re-raise (or raise a new exception), the client gets 500 and nothing is logged: **always `raise`**.
  - A `scope="request"` dependency's sub-dependencies must also be `request` scoped.
- Router-level/global dependencies: `APIRouter(dependencies=[...])`, `FastAPI(dependencies=[...])`.

## Async vs sync endpoints

- Use `async def` when the body awaits async libraries; use plain `def` for blocking libraries (FastAPI runs `def` path functions/dependencies in a threadpool). Docs: https://fastapi.tiangolo.com/async/ (page fetched only partially; the threadpool statement is from memory -> UNVERIFIED in this pass).
- Never block the event loop in `async def` (sync DB/HTTP clients, `time.sleep`). If an `async def` endpoint must call a sync client (e.g. Firestore sync client), wrap with `starlette.concurrency.run_in_threadpool` (exposed in `fastapi.concurrency`) - UNVERIFIED against starlette.io/fastapi docs in this pass.
- Background task functions may be `def` or `async def` (verified).

## Settings / config

https://fastapi.tiangolo.com/advanced/settings/ and pydantic-settings docs (https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/):

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "example-service"
    api_v1_prefix: str = "/api/v1"
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 30
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- Install `pydantic-settings` (also pulled by `fastapi[all]` per docs).
- Env var names are case-insensitive by default (`APP_NAME` -> `app_name`); `env_prefix`, `env_nested_delimiter="__"`, `case_sensitive` are available. Complex types (list/dict/submodel) are parsed as JSON; use `NoDecode` + `BeforeValidator` for comma-separated lists.
- Unlike `BaseModel`, `BaseSettings` validates default values by default.
- Misspelled env vars are silently ignored even with `extra="forbid"` (they just don't match any field) - verified in pydantic-settings docs.
- Use `Depends(get_settings)` so tests can override via `dependency_overrides`; keep secrets in env, not defaults; use lower-case field names.

## Error handling

https://fastapi.tiangolo.com/tutorial/handling-errors/ (verified: `raise HTTPException(status_code=404, detail="...")`; it is raised, not returned).

```python
class DuplicateEmailError(Exception): ...

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DuplicateEmailError)
    async def handle_duplicate(request: Request, exc: DuplicateEmailError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "Email already registered"})
```

- `HTTPException` for route-level HTTP concerns; domain exceptions for service invariants; central handlers when many routes map the same failure.
- Don't swallow exceptions in yield dependencies (see above). Avoid broad `except Exception` around DB/session logic.

## Auth pointers

- Use `fastapi.security` (`OAuth2PasswordBearer`, scopes, HTTP Basic): https://fastapi.tiangolo.com/tutorial/security/ and https://fastapi.tiangolo.com/advanced/security/oauth2-scopes/. Router-level `dependencies=[Depends(get_current_user)]` protects a whole group.
- Keep token decode/validation in a focused helper; decide once what JWT `sub` means (string user id) and keep encode/decode consistent; reference settings that exist.
- Old reference used `passlib` + `PyJWT` (`jwt.encode(..., algorithm="HS256")`, `datetime.now(UTC)`); current FastAPI docs' recommended password-hashing library was NOT re-checked -> UNVERIFIED; check https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ before copying.
- Authorization design (roles, ownership checks): see `application-authorization`. Keep checks explicit at route or service boundary.

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                           session: Annotated[AsyncSession, Depends(get_db_session)]):
    user_id = decode_and_validate_user_id(token, settings.secret_key)   # your helper
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials")
    return user
```

## Lifespan & background tasks

Lifespan (https://fastapi.tiangolo.com/advanced/events/): `FastAPI(lifespan=...)` takes an async context manager; `startup`/`shutdown` event handlers are listed as **deprecated** alternatives. Don't rewrite a repo's coherent existing handlers without reason.

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = get_settings()
    try:
        yield
    finally:
        await dispose_engine()

app = FastAPI(title="Example Service", version="0.1.0", lifespan=lifespan)
```

- Only initialize resources the app owns; avoid scattered global mutable state.
- Lifespan runs on graceful shutdown only if the server process receives signals: in Docker use exec-form `CMD` (verified, deployment/docker).

`BackgroundTasks` (https://fastapi.tiangolo.com/tutorial/background-tasks/, verified): declare a `BackgroundTasks` parameter (works in dependencies too; tasks merge), `add_task(func, *args, **kwargs)`; tasks run after the response. Class is Starlette's (docs now at starlette.dev/background/). For heavy / cross-process work use a queue (Celery etc.), per the docs caveat. Tasks run in-process: lost if the process dies; on Cloud Run CPU may be throttled after the response (UNVERIFIED here, see Cloud Run section).

## Async SQLAlchemy (kept from old reference)

SQLAlchemy 2.x claims not re-verified (outside allowed primary doc set) -> UNVERIFIED. FastAPI's own SQL tutorial uses SQLModel: https://fastapi.tiangolo.com/tutorial/sql-databases/.

```python
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
class Base(DeclarativeBase): pass

async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session

async def dispose_engine() -> None:
    await engine.dispose()
```

- Commit in the service layer / explicit unit of work; don't hide writes in a generic dependency.
- Repositories bound to a session (`UserRepository(session)` with `get_by_id`, `get_by_email`, `add` -> `flush()` + `refresh()`); services raise domain exceptions (`DuplicateEmailError`); keep transport schemas distinct from ORM models.

Thin route example:

```python
router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, service: UserServiceDep) -> UserRead:
    try:
        user = await service.create_user(payload)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=409, detail="Email already registered") from exc
    return UserRead.model_validate(user)
```

## Testing

Sync: `TestClient` (https://fastapi.tiangolo.com/tutorial/testing/), verified:

```python
from fastapi.testclient import TestClient
client = TestClient(app)
def test_read_main():
    r = client.get("/"); assert r.status_code == 200
```

Async (https://fastapi.tiangolo.com/advanced/async-tests/, verified): `@pytest.mark.anyio` + `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`. Inside async tests you cannot use `TestClient`. `AsyncClient` does **not** trigger lifespan events; use `LifespanManager` from `asgi-lifespan` (docs-recommended). `TestClient` lifespan via `with TestClient(app)` per https://fastapi.tiangolo.com/advanced/testing-events/ - page not fetched -> UNVERIFIED.

Dependency overrides (https://fastapi.tiangolo.com/advanced/testing-dependencies/; page text was truncated, only the `app.dependency_overrides` attribute confirmed):

```python
app.dependency_overrides[get_db_session] = override_get_db_session
# teardown:
app.dependency_overrides.clear()
```

- Override session/settings/external-service dependencies; create tables only in integration tests; unit-test services without HTTP; add targeted regression tests; if you modernize wiring, modernize test transport and overrides too.
- Anyio backend fixture (asyncio only vs trio) may need configuring - UNVERIFIED.
- TDD workflow: see `test-driven-development`.

## OpenAPI customization

https://fastapi.tiangolo.com/tutorial/metadata/ (verified):
- `FastAPI(title, summary, description (Markdown), version, terms_of_service, contact, license_info)`; `license_info` takes `identifier` (SPDX) **or** `url`, mutually exclusive.
- `openapi_tags=[{"name", "description", "externalDocs"}]`; list order sets docs UI order.
- `openapi_url` (default `/openapi.json`; `None` disables schema and docs UIs), `docs_url` (`/docs`), `redoc_url` (`/redoc`); each may be set to `None`.
- Per-route: `tags`, `summary`, `responses={404: {...}}`, `status_code`, `response_model`; in production consider disabling docs for internal-only APIs.
- Design/governance of the contract: see `openapi-specification`.

## Production

- **Run command.** `fastapi run app/main.py` (or `fastapi run` with entrypoint in pyproject); `fastapi dev` for development. `--workers N` starts multiple Uvicorn workers (https://fastapi.tiangolo.com/deployment/server-workers/, verified).
- **Containers** (https://fastapi.tiangolo.com/deployment/docker/, verified): build from the official Python image, copy requirements first for layer caching, use **exec-form** `CMD ["fastapi", "run", "app/main.py", "--port", "80"]` (shell form breaks graceful shutdown/lifespan). On Kubernetes-style platforms with cluster-level replication use **one process per container**, no `--workers`. Use workers only for single-server/Docker Compose setups. The `tiangolo/uvicorn-gunicorn-fastapi` image is **deprecated**; Gunicorn+Uvicorn-worker is no longer needed just for worker management (docs). If you still choose gunicorn, `-k uvicorn.workers.UvicornWorker` syntax is UNVERIFIED here.
- **Proxy headers** (https://fastapi.tiangolo.com/advanced/behind-a-proxy/, verified): servers don't trust `X-Forwarded-For/Proto/Host` by default. Pass `--forwarded-allow-ips="*"` (only when only the trusted proxy can reach the server) or `--proxy-headers` as shown in the Docker page, otherwise redirects (e.g. `/items` -> `/items/`) point to `http://`. The `root_path` parameter of `FastAPI()` is deprecated (0.146); use `fastapi run --root-path /api/v1`.
- **Logging/observability**: structured logs and correlation IDs are in `python-observability`. Its FastAPI middleware sketch (`async def correlation_middleware(request, call_next)` that sets an `X-Correlation-ID` contextvar and echoes the header) needs registering via `@app.middleware("http")` / `app.add_middleware` - UNVERIFIED registration detail (see https://fastapi.tiangolo.com/tutorial/middleware/). Docs also have OpenTelemetry: https://fastapi.tiangolo.com/advanced/opentelemetry/.
- **Health checks**: expose a cheap `GET /health` (no DB); optional separate readiness route that checks dependencies. Keep it under test (HealthResponse model example below). Orchestrator probe config is platform-specific - UNVERIFIED.
- **Pre-start steps** (migrations) belong in an init container/separate job when running replicated containers (docker page, verified).

```python
class HealthResponse(BaseModel):
    status: str

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")
```

## Cloud Run + Firestore (condensed from fastapi-cloudrun-firestore.md)

All of this section is from the old reference and is UNVERIFIED (Google Cloud docs are outside the allowed primary-source set for this pass).

- Keep the service stateless; separate settings, API routing, Firestore repository. Reuse the Firestore client via a cached dependency (not per request).
- If endpoints are `async` but the Firestore client is synchronous, call repository methods through `run_in_threadpool` (or use plain `def` routes / the async client).
- Env config: `GOOGLE_CLOUD_PROJECT`, `FIRESTORE_DATABASE`, `FIRESTORE_COLLECTION`; `GOOGLE_APPLICATION_CREDENTIALS` (absolute path) for local runs with a key file. Terraform inputs from env: `TF_VAR_project_id`, `TF_VAR_region`. Document all of them in the README.
- Throughput baseline for ~50 RPS: lightweight handlers, reused client, Cloud Run concurrency ~40, min/max instances; validate with load tests in the target project. A baseline, not an SLA.
- A named Firestore database is valid when deliberately avoiding `(default)`.
- Tests mock/override the repository boundary (via `dependency_overrides`) so they run without GCP credentials.
- README checklist: local `uv` setup, run command, credential-free test command, Docker/Cloud Run container run example, Terraform apply flow, exact env vars (local + deploy), note that the image may already exist in Artifact Registry rather than being built by Terraform.
- Cloud Run also needs the app to listen on the `PORT` it provides (UNVERIFIED; check `fastapi run --port $PORT` handling) and exec-form `CMD` (verified generally).

## Pitfalls

1. Pydantic v1 idioms (`.dict()`, `class Config`) in v2 code.
2. Returning ORM models directly; no response schema.
3. Implicit commits in a generic DB dependency.
4. Fat routes; business rules belong in services.
5. Turning every helper into a `Depends`; abstractions (repositories/services) added with no value; starting with too much architecture.
6. Swallowing exceptions in `yield` dependencies (500 with no logs) - always re-raise.
7. Blocking calls inside `async def` handlers.
8. Inconsistent JWT `sub` conventions; auth code referencing undefined settings objects.
9. Shell-form `CMD` in Dockerfile (no graceful shutdown/lifespan); forgetting proxy headers behind a load balancer (wrong https redirects); `--workers` on top of cluster replication.
10. `AsyncClient` tests relying on lifespan resources without `LifespanManager`.
11. Copying outdated examples: deprecated `on_event`, `root_path=` argument, `Query(custom=...)` extras, non-`Annotated` deps, old `tiangolo` Docker image; upgrading structure without upgrading tests.
12. Misspelled env vars silently ignored by pydantic-settings.
13. Existing repo conventions overridden without being asked.

## Verification checklist

- [ ] Repo confirmed as FastAPI (`FastAPI`, `APIRouter`, `uvicorn`); existing conventions kept.
- [ ] Pydantic v2 patterns used when project is on v2; settings via `SettingsConfigDict`.
- [ ] Request/response schemas, services, persistence models have clear boundaries.
- [ ] Errors map to stable HTTP responses; yield dependencies re-raise.
- [ ] Auth wiring references real settings/helpers; tests cover happy path + changed behavior.
- [ ] Lifespan resources disposed; Docker CMD exec form; proxy headers configured if behind LB.
- [ ] Ran `pytest`, `ruff`, `mypy` per `python-dev`.

## See also

- python-dev references (originals, retained): `references/fastapi-layout.md`, `references/fastapi-production-patterns.md`, `references/fastapi-cloudrun-firestore.md`; also `python-dev/python-observability`.
- Related skills: `python-dev`, `python-observability`, `openapi-specification`, `application-authorization`, `aws-agentic-ai` (AWS-hosted agent/service deployment), `test-driven-development`.
- Primary docs: https://fastapi.tiangolo.com/ , https://docs.pydantic.dev/ , https://www.starlette.io/ (Starlette docs also at starlette.dev; not directly fetched).
