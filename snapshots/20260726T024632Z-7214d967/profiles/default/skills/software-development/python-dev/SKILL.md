---
name: python-dev
description: Use when building or modifying Python projects, services, Lambda handlers, or CLIs with Hermes-native repo inspection, uv-based workflows, typing, testing, and deployment hygiene.
version: 1.5.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [python, fastapi, lambda, cli, uv, typing, testing, docker]
    related_skills: [test-driven-development, systematic-debugging, python-debugpy, requesting-code-review]
---

# Python Development

## Overview

Use this skill when Hermes is asked to inspect, build, modify, or standardize Python codebases. It is for implementation work: discover the actual project structure, identify the active toolchain, edit the right files, run the right checks, and leave the repo in a verifiable state.

The core stance is Hermes-native and repo-first: inspect before editing, prefer the repository's existing conventions when they are coherent, use Hermes file tools for code work, and verify before declaring success.

## When to Use

- Building or editing Python applications or libraries
- Adding or changing FastAPI endpoints
- Writing or fixing AWS Lambda handlers in Python
- Building CLI tools with typer, argparse, click, or rich
- Creating or cleaning up Python project structure
- Adding tests, typing, packaging, or Docker assets
- Modernizing older Python repos toward `pyproject.toml` + `uv`

Do not use this skill for:
- Pure planning with no implementation changes
- Non-Python projects
- Deep root-cause debugging when `systematic-debugging` should drive the task
- Strict test-first execution when `test-driven-development` should be primary

## Hermes Workflow

### 1. Inspect before editing

Do not assume layout, toolchain, or test commands. Inspect the repo first:

- find Python files and project manifests
- read `pyproject.toml`, `README.md`, and relevant config files
- identify framework and entrypoints from actual code
- reuse existing repo conventions when they are coherent

Typical discovery targets:

- `pyproject.toml`
- `uv.lock`
- `requirements.txt`
- `setup.py`
- `setup.cfg`
- `pytest.ini`
- `mypy.ini`
- `ruff.toml` or `.ruff.toml`
- `.env.example`
- `Dockerfile`
- `README.md`
- likely entrypoints such as `app/main.py`, `main.py`, `handler.py`, or `cli/main.py`

### 2. Prefer Hermes file tools for code work

Use:

- `search_files` to discover files and patterns
- `read_file` to inspect code and config
- `patch` for targeted edits
- `write_file` for full-file creation or rewrites
- `terminal` only for commands that must execute: tests, linters, package tools, git status, Docker builds

### 3. Match the repo before imposing a template

If the repo already uses a coherent stack, extend it instead of forcing a different one.

Examples:
- keep `pytest` if the repo uses `pytest`
- keep `ruff` if the repo uses `ruff`
- keep the current package layout if imports and tooling depend on it
- only introduce `uv` or `pyproject.toml` migration when the task asks for it or the repo is clearly under-structured

### 4. Verify with the real project commands

Before finishing, run the smallest meaningful verification available:

- targeted test for changed behavior
- broader test or suite when feasible
- lint or type checks if configured
- import or startup smoke test if no formal tests exist

Report what ran and what remains unverified.

## Opinionated Defaults for New Projects

When creating a new Python project from scratch and the user has not specified a different stack, prefer:

- Python 3.11+
- `uv` for dependency management and execution
- `pyproject.toml` as the source of truth
- `pytest` for tests
- `ruff` for linting and formatting
- `mypy` when the codebase benefits from static typing checks
- FastAPI for HTTP APIs
- Pydantic v2 for schema validation
- typer for CLIs
- rich for CLI output
- `.env.example` for local environment documentation

These are greenfield defaults, not a reason to rewrite an established repo that already has coherent conventions.

## Python Decision Rules

### Dependency management

Prefer `uv` for new or modernized Python projects.

Guidance:
- keep `pyproject.toml` as the source of truth
- avoid ad hoc `pip install` flows for project dependencies
- only generate `requirements.txt` when an external deploy target truly requires it
- if the repo uses a `src/` layout, include a `[build-system]` table in `pyproject.toml`; otherwise `uv sync` can install dependencies without installing the project itself, leaving the application package off import resolution
- when creating a local `.venv`, prefer targeting that interpreter explicitly for installs if there is any ambiguity about the active environment

Example:

```bash
uv venv
uv pip install --python .venv/bin/python -e .[dev]
```

This is safer than assuming `uv pip install -e .[dev]` will always target the intended project venv, especially on hosts that may already have another active Python environment.

For starter structure and settings, use `references/pyproject-template.md`.

### Framework detection

Infer the project type from the repo before editing:

- FastAPI: look for `FastAPI`, `APIRouter`, `uvicorn`
- Lambda: look for `handler(event, context)`, `template.yaml`, SAM/CDK/serverless files
- CLI: look for `typer`, `click`, `argparse`, or `__main__` entrypoints

For opinionated greenfield layouts, use:
- `references/fastapi-layout.md`
- `references/fastapi-production-patterns.md` when a FastAPI service needs deeper production wiring guidance
- `references/fastapi-cloudrun-firestore.md` when the service is a small GCP/Cloud Run/Firestore showcase and should document env-driven deploy inputs plus credential handling clearly
- `references/lambda-layout.md`
- `references/cli-layout.md`

### Typing and structure

- add parameter and return annotations to new or edited functions
- prefer concrete types over `Any`
- keep modules focused
- separate interface code from business logic when the codebase size justifies it
- avoid turning `utils.py` into a catch-all module

### Configuration and secrets

- read secrets and environment-specific config from environment variables
- provide `.env.example` when local setup needs configuration
- do not hardcode tokens, passwords, or deployment-specific values

### Logging

- follow existing logging conventions in the repo
- if no convention exists, prefer centralized or structured logging over scattered prints
- remove temporary debug prints before finishing

## Verification and Packaging

Prefer the repo's existing test entrypoint. If none is documented, infer it from the manifest and filesystem.

Verification order:
1. run focused checks for the changed area
2. run broader checks if they are fast and available
3. if no test suite exists, run the lightest useful smoke test
4. report what was run, what passed, and any remaining gaps

For reusable verification guidance, use `references/verification-playbook.md`.

If the user explicitly wants TDD, load and follow `test-driven-development` as the primary execution model.

Add Docker assets when the project is deployable as a service or the task asks for containerization.

General guidance:
- prefer multi-stage builds
- use slim base images
- run as non-root when practical
- copy only what the runtime needs
- include `.dockerignore`
- lint Dockerfiles when `hadolint` is available

For starter Dockerfile guidance, use `references/dockerfile-template.md`.

## README Expectations

When creating or substantially changing a Python project, ensure `README.md` covers the actual workflow used by the repo:

- project purpose
- prerequisites
- install/setup commands
- local run commands
- environment variables
- test commands
- deployment notes when relevant

Do not paste generic instructions that do not match the repository.

## Included References

This skill ships with linked references for reusable detail:

- `references/greenfield-project-checklist.md` — greenfield Python project checklist
- `references/pyproject-template.md` — starter `pyproject.toml` structure for uv/pytest/ruff/mypy
- `references/fastapi-layout.md` — opinionated FastAPI file/layout guidance
- `references/fastapi-production-patterns.md` — deeper FastAPI production patterns for settings, async SQLAlchemy, DI boundaries, auth, error handling, and tests
- `references/fastapi-cloudrun-firestore.md` — greenfield pattern for small FastAPI services deployed to Cloud Run with Firestore, env-driven Terraform inputs, repository mocking for tests, and a moderate-concurrency baseline
- `references/lambda-layout.md` — opinionated AWS Lambda file/layout guidance
- `references/cli-layout.md` — opinionated Python CLI file/layout guidance
- `references/dockerfile-template.md` — Python container/Dockerfile starter guidance
- `references/verification-playbook.md` — lightweight verification flow for Python changes

## Host-Specific Rules

### New project location

When creating a new project on this host, place it under:

```bash
/Users/miqui/development
```

### Git workflow on hosts with a required wrapper

If repository creation, push, or PR actions in the active environment must go through a local wrapper, load and follow `local-git-workflow` instead of embedding the host-specific policy here.

## Suggested External References

Use or cite these when deeper framework- or tooling-specific guidance is needed:

- Python packaging and `pyproject.toml`: https://packaging.python.org/
- Astral `uv` docs: https://docs.astral.sh/uv/
- Pytest docs: https://docs.pytest.org/
- Ruff docs: https://docs.astral.sh/ruff/
- FastAPI docs: https://fastapi.tiangolo.com/
- Pydantic docs: https://docs.pydantic.dev/
- Typer docs: https://typer.tiangolo.com/
- Python Morsels articles: https://www.pythonmorsels.com/articles/browse/ — practical advice on idiomatic Python, iteration, refactoring, and readable function design
- AWS Lambda Python docs: https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html

## Common Pitfalls

1. Editing before inspecting the repo's actual layout and tooling
2. Forcing a new stack onto a repo that already has coherent conventions
3. Using shell text-processing instead of Hermes file tools for code inspection and edits
4. Adding dependencies without updating the project manifest
5. Leaving functions untyped in otherwise typed code
6. Hardcoding secrets or environment-specific configuration
7. Declaring success without running meaningful verification
8. Writing generic README or Docker instructions that do not match the repo
9. Using raw git or PR commands when the host requires a dedicated local wrapper skill such as `local-git-workflow`
10. Assuming `uv pip install` will target the project `.venv` without verification
11. Documenting `uv` commands that differ from the interpreter path actually used during verification

## Verification Checklist

- [ ] Repo structure and tooling were inspected before edits
- [ ] Changes match the repo's existing conventions or intentionally improve them
- [ ] Dependencies and config were updated in the right files
- [ ] New or changed Python code includes appropriate typing
- [ ] The changed behavior was verified with tests, linting, or smoke checks
- [ ] Any README or Docker updates match the actual project workflow
- [ ] Any required repo creation, push, or PR action uses `local-git-workflow` when the active host mandates a wrapper-based workflow
