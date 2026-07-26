# Greenfield Python Project Checklist

Use this when creating a new Python project from scratch.

## Core setup

- Create the project under `/Users/miqui/development`
- Initialize with `uv`
- Add runtime dependencies first, then dev dependencies
- Keep `pyproject.toml` as the source of truth
- Add `.env.example` if configuration is required

## Minimum quality bar

- Type hints on new public functions
- `pytest` wired and runnable
- `ruff` configured or runnable
- `README.md` explains setup and run commands
- No secrets committed

## If it is an API

- Prefer FastAPI
- Keep routes thin
- Put business logic in services
- Validate I/O with Pydantic models
- Add at least one smoke or route test

## If it is a CLI

- Prefer typer unless the repo already uses another CLI framework
- Keep formatting/output near the command boundary
- Keep core logic importable and testable

## If it is deployable

- Add `Dockerfile`
- Add `.dockerignore`
- Verify the container can build

## Before declaring success

- Run at least one meaningful verification command
- Confirm the README matches the actual commands used
- If repo creation, push, or PR is needed and the active host uses a wrapper policy, follow `local-git-workflow`
