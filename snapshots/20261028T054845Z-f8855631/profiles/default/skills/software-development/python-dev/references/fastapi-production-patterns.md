# FastAPI Production Patterns

Use this reference when `python-dev` is being applied to a FastAPI service and you need more than the minimal starter layout in `references/fastapi-layout.md`.

This file is intentionally **not** a second full Python-project skill. It complements `python-dev` by focusing on modern FastAPI-specific implementation patterns for production services: app wiring, settings, dependency boundaries, async SQLAlchemy, error handling, auth wiring, and testing.

## When to Reach for This Reference

Use this reference for tasks like:

- creating a new FastAPI service with production-oriented structure
- modernizing an older FastAPI project toward Pydantic v2 and current SQLAlchemy async patterns
- adding service/repository boundaries to a growing API codebase
- wiring auth, lifespan, database sessions, and exception handling consistently
- improving test structure for FastAPI apps using async dependencies

Do not use this reference to override an existing repo that already has a coherent framework-specific architecture unless the task explicitly asks for restructuring.

## Scope Boundary with `python-dev`

`python-dev` remains the primary skill for:

- repo inspection before edits
- choosing the project toolchain
- dependency management with `uv`
- README, Docker, linting, typing, and verification expectations
- adapting to the repository’s actual conventions

This reference adds **FastAPI-specific depth** once the project is known to be a FastAPI service.

## Recommended Layout for a Growing Service

For small services, a flat `routers/` + `schemas/` + `services/` layout is fine. As the service grows, prefer a structure like:

```text
project/
  app/
    api/
      dependencies.py
      router.py
      routes/
        auth.py
        health.py
        users.py
    core/
      config.py
      database.py
      logging.py
      security.py
      exceptions.py
    db/
      base.py
      models/
        user.py
    repositories/
      user_repository.py
    schemas/
      auth.py
      user.py
    services/
      auth_service.py
      user_service.py
    main.py
  tests/
    integration/
      test_health.py
      test_users.py
    unit/
      test_user_service.py
  pyproject.toml
  .env.example
  README.md
```

### Layout notes

- `api/routes/` handles HTTP concerns only: request parsing, response models, status codes, auth requirements.
- `services/` owns business rules and orchestration.
- `repositories/` owns persistence queries and storage-specific logic.
- `core/` holds app-wide wiring: settings, DB engine/session setup, security helpers, logging, and shared exceptions.
- `db/models/` holds SQLAlchemy ORM models when the project is large enough to justify separation.
- `api/dependencies.py` should contain composable request-time dependencies, not business logic.

Avoid creating layers just to look enterprise. Only split routes/services/repositories when the complexity justifies it.

## App Wiring with Lifespan

Prefer the lifespan API over older startup/shutdown event handlers for new projects.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = get_settings()
    app.state.settings = settings
    try:
        yield
    finally:
        await dispose_engine()


app = FastAPI(
    title="Example Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)
```

### Notes

- Store durable app-wide objects intentionally; do not scatter global mutable state.
- Only initialize expensive resources in lifespan if the app truly owns them.
- If the repo already uses startup/shutdown events coherently, do not rewrite them without a reason.

## Settings with Pydantic v2

Prefer `pydantic-settings` with explicit config via `SettingsConfigDict`.

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "example-service"
    api_v1_prefix: str = "/api/v1"
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### Notes

- Prefer lower-case field names in Python unless the repo has a strong env-mirroring convention.
- Let environment variable mapping happen through Pydantic rather than carrying all-caps names through application code.
- Keep secrets in the environment, not in defaults.

## Async SQLAlchemy Session Pattern

For SQLAlchemy 2.x async usage, prefer `async_sessionmaker`, `DeclarativeBase`, and a request-scoped session dependency.

```python
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def dispose_engine() -> None:
    await engine.dispose()
```

### Notes

- Prefer committing in the service layer or an explicit unit-of-work boundary when the operation semantics matter.
- Do not hide writes inside a generic dependency if the codebase needs precise transaction control.
- For simple apps, a single request-scoped session dependency is enough.

## Dependency Boundaries

Use FastAPI dependencies for request-time concerns and wiring, not to hide business behavior.

Good dependency uses:

- current authenticated principal
- DB session acquisition
- pagination/filter parsing
- loading shared service instances with lightweight constructors

Avoid:

- burying core business decisions inside dependency functions
- assembling large object graphs in every route without need
- creating pseudo-framework DI abstractions that fight FastAPI’s native style

Example:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


def get_user_service(
    session: AsyncSession = Depends(get_db_session),
) -> UserService:
    repository = UserRepository(session)
    return UserService(repository)
```

This is appropriate when service construction is cheap and explicit.

## Repository and Service Pattern

Prefer repositories that are bound to a session instance rather than methods that require passing the session repeatedly.

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
```

```python
from app.core.security import hash_password
from app.db.models.user import User
from app.schemas.user import UserCreate
from app.services.errors import DuplicateEmailError


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def create_user(self, payload: UserCreate) -> User:
        existing = await self.repository.get_by_email(payload.email)
        if existing is not None:
            raise DuplicateEmailError(payload.email)

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
        )
        return await self.repository.add(user)
```

### Notes

- Keep transport schemas (`UserCreate`) distinct from persistence models (`User`).
- Do not mutate request schema instances into database objects when a direct model construction is clearer.
- Prefer domain-specific exceptions over raw `ValueError` for business-rule failures.

## Error Handling

Prefer explicit exception types plus centralized exception handlers for stable API behavior.

```python
class DuplicateEmailError(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email already registered: {email}")
```

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.errors import DuplicateEmailError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DuplicateEmailError)
    async def handle_duplicate_email(
        request: Request,
        exc: DuplicateEmailError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "Email already registered"},
        )
```

### Notes

- Use `HTTPException` for route-level HTTP concerns.
- Use domain exceptions for service-layer invariants.
- Central handlers are useful when multiple routes share the same failure mapping.

## Auth and Security Wiring

Keep security primitives small and explicit.

```python
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str, secret_key: str, expires_minutes: int) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)
```

Dependency example:

```python
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.repositories.user_repository import UserRepository

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    user_id = decode_and_validate_user_id(token, settings.secret_key)
    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return user
```

### Notes

- Keep token decode/validation in a focused helper instead of bloating the dependency.
- Be consistent about whether `sub` stores a string user ID or another principal identifier.
- Do not reference undefined settings objects inside auth wiring.

## Route Pattern

Routes should stay thin.

```python
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_user_service
from app.schemas.user import UserCreate, UserRead
from app.services.errors import DuplicateEmailError
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    try:
        user = await service.create_user(payload)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=409, detail="Email already registered") from exc
    return UserRead.model_validate(user)
```

### Notes

- Prefer response schemas such as `UserRead` rather than returning ORM models directly.
- In Pydantic v2, use `model_validate()` with `from_attributes=True` configured on the response model when appropriate.
- Keep authorization checks explicit at the route or service boundary.

## Pydantic v2 Schema Pattern

Prefer explicit read/write schemas and modern config.

```python
from pydantic import BaseModel, ConfigDict, EmailStr


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

### Notes

- Prefer `model_dump()` over `.dict()` in application code.
- Prefer `model_validate()` over older ORM conversion idioms when targeting Pydantic v2.
- Keep input and output schemas separate when fields differ in sensitivity or shape.

## Testing Patterns

Prefer async tests with explicit dependency overrides and modern `httpx` transport wiring.

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

For DB-backed tests:

- override the session dependency with a test session
- create tables only for integration-style tests
- keep unit tests for services independent of HTTP where practical
- prefer targeted regression tests when fixing bugs

## FastAPI-Specific Pitfalls

1. **Using outdated Pydantic v1 idioms in new code.** Prefer `model_dump()`, `model_validate()`, and `ConfigDict`/`SettingsConfigDict` for Pydantic v2 codebases.
2. **Returning ORM models directly without explicit response schemas.** This couples transport shape to persistence shape.
3. **Committing transactions implicitly in a generic DB dependency.** Keep transaction boundaries explicit when behavior matters.
4. **Putting too much logic in routes.** Route handlers should orchestrate HTTP concerns, not own core business rules.
5. **Turning every helper into a dependency.** Use dependencies for request-time wiring, not as a replacement for ordinary Python composition.
6. **Building repository abstractions that add no value.** Introduce repositories when queries or storage concerns justify them.
7. **Using broad `except Exception` flows around DB/session logic without a clear error strategy.** Catch specific failures where possible.
8. **Mixing auth token structure conventions.** Decide what `sub` means and keep encode/decode logic consistent.
9. **Modernizing structure without modernizing tests.** If you upgrade app wiring, update test transport and dependency override patterns too.

## Verification Checklist

- [ ] The repo was confirmed to be FastAPI before applying these patterns
- [ ] Existing project conventions were preserved unless the task explicitly called for restructuring
- [ ] New settings code uses current Pydantic v2 patterns when the project is on Pydantic v2
- [ ] New SQLAlchemy async code uses `async_sessionmaker` and `DeclarativeBase` when appropriate
- [ ] Request schemas, response schemas, services, and persistence models have clear boundaries
- [ ] Error handling maps business failures to stable HTTP responses intentionally
- [ ] Auth wiring references concrete settings and helper functions that actually exist
- [ ] Tests cover at least one happy path and any changed or regressed behavior
